"""CU17: loyalty points per company (1 point per 10 Bs paid, 10 points = 1 Bs, tiers by lifetime points)."""
from decimal import Decimal

import pytest

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_marketplace_transactions import add, call, checkout as web_checkout, market, market_api, pay, rejected  # noqa: F401


@pytest.fixture
def loyalty_api(market_api):
    from app.routes import loyalty_routes

    market_api.app.include_router(loyalty_routes.router, prefix="/api")
    return market_api


@pytest.fixture
def pricey(api_db, market):
    market.own.variant.price = 250  # 25 points per unit
    api_db.commit()
    return market


def give_points(db, market, points):
    from app.models.loyalty import LoyaltyAccount

    db.add(LoyaltyAccount(tenant_id=market.own.tenant.id, user_id=market.customer.id,
                          points_balance=points, lifetime_points=points))
    db.commit()


def balance(api, market):
    rows = call(api, market.customer, "GET", "/loyalty/balance", expected_message="Puntos obtenidos exitosamente")
    return {row["tenant_name"]: (row["points_balance"], row["lifetime_points"], row["tier"]) for row in rows}


def checkout(api, market, points=0):
    return web_checkout(api, market, points_to_redeem=points)


def test_tiers_and_conversions():
    from app.services.loyalty_service import points_for, points_value, tier_for

    assert [tier_for(p) for p in (0, 499, 500, 1499, 1500)] == ["Bronce", "Bronce", "Plata", "Plata", "Oro"]
    assert points_for(Decimal("249.99")) == 24 and points_value(55) == Decimal("5.50")


def test_paid_web_order_earns_points_once(loyalty_api, api_db, pricey):
    add(loyalty_api, pricey)
    order = checkout(loyalty_api, pricey)
    assert balance(loyalty_api, pricey) == {}  # nothing earned while unpaid
    pay(loyalty_api, pricey, order)
    assert balance(loyalty_api, pricey) == {pricey.own.tenant.name: (25, 25, "Bronce")}
    history = call(loyalty_api, pricey.customer, "GET", "/loyalty/transactions")
    assert [(row["type"], row["points"], row["source_id"]) for row in history] == [("earn", 25, order["id"])]


def test_redeemed_points_discount_the_order_and_return_when_cancelled(loyalty_api, api_db, pricey):
    give_points(api_db, pricey, 100)
    add(loyalty_api, pricey)
    order = checkout(loyalty_api, pricey, points=50)
    assert Decimal(str(order["loyalty_discount"])) == Decimal("5.00")
    assert Decimal(str(order["total_amount"])) == Decimal("245.00")
    assert balance(loyalty_api, pricey)[pricey.own.tenant.name][0] == 50
    call(loyalty_api, pricey.customer, "POST", f"/orders/{order['id']}/cancel")
    assert balance(loyalty_api, pricey)[pricey.own.tenant.name][0] == 100


def test_invalid_redemptions_are_rejected_without_side_effects(loyalty_api, api_db, pricey):
    add(loyalty_api, pricey)
    body = {"pickup_branch_id": str(pricey.branches[0].id)}
    rejected(loyalty_api, api_db, pricey.customer, "POST", "/payments/qr/checkout", 400,
             "Puntos insuficientes: tienes 0 puntos en esta empresa", json={**body, "points_to_redeem": 10})
    give_points(api_db, pricey, 5000)
    rejected(loyalty_api, api_db, pricey.customer, "POST", "/payments/qr/checkout", 400,
             "Los puntos se canjean en múltiplos de 10", json={**body, "points_to_redeem": 15})
    rejected(loyalty_api, api_db, pricey.customer, "POST", "/payments/qr/checkout", 400,
             "Los puntos canjeados superan el monto a pagar", json={**body, "points_to_redeem": 2510})
    assert balance(loyalty_api, pricey)[pricey.own.tenant.name][0] == 5000


def test_till_redeems_and_earns_for_an_identified_customer(loyalty_api, api_db, market):
    give_points(api_db, market, 100)
    cashier = market.staff[0, "cajero"]
    found = call(loyalty_api, cashier, "GET", "/loyalty/customer", params={"email": market.customer.email})
    assert (found["points_balance"], found["tier"]) == (100, "Bronce")
    item = {"variant_id": str(market.own.variant.id), "quantity": 1}  # price 25
    sale = call(loyalty_api, cashier, "POST", "/sales/", 201,
                json={"items": [item], "customer_email": market.customer.email, "points_to_redeem": 100})
    assert Decimal(str(sale["total_amount"])) == Decimal("15.00")
    # 100 redeemed, 1 earned on the 15 Bs paid.
    assert balance(loyalty_api, market) == {market.own.tenant.name: (1, 101, "Bronce")}
    rejected(loyalty_api, api_db, cashier, "POST", "/sales/", 400,
             "Ingresa el correo del cliente registrado para canjear puntos",
             json={"items": [item], "points_to_redeem": 10})


def test_points_are_kept_per_company(loyalty_api, api_db, market):
    give_points(api_db, market, 40)
    foreign_cashier = market.staff[2, "cajero"]
    found = call(loyalty_api, foreign_cashier, "GET", "/loyalty/customer", params={"email": market.customer.email})
    assert found["points_balance"] == 0
