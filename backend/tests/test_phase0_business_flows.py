"""Phase 0 regressions: paid-order hand-over, visit date window, stock constraints."""
from datetime import date, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_marketplace_transactions import add, call, market, market_api, rejected, stock  # noqa: F401


def _stripe_paid_order(api, db, market):
    from app.models.order import Order
    from app.schemas.order_schema import PaymentMethodEnum
    from app.services.order_service import _consume_order

    add(api, market)
    created = call(api, market.customer, "POST", "/payments/cash/checkout", 201,
                   json={"pickup_branch_id": str(market.branches[0].id)})
    order = db.query(Order).filter(Order.id == created["id"]).one()
    order.payment_method = PaymentMethodEnum.stripe
    _consume_order(db, order)  # what the Stripe webhook does on payment_intent.succeeded
    db.commit()
    return created


def test_stripe_paid_order_is_handed_over_with_pickup_code(market_api, api_db, market):
    order = _stripe_paid_order(market_api, api_db, market)
    call(market_api, market.staff[0, "encargado"], "POST", f"/orders/{order['id']}/ready")
    before = stock(api_db, market.own.variant, market.branches[0])

    rejected(market_api, api_db, market.staff[0, "cajero"], "POST", f"/orders/{order['id']}/hand-over",
             400, "Código de retiro inválido", json={"pickup_code": "wrong"})
    handed = call(market_api, market.staff[0, "cajero"], "POST", f"/orders/{order['id']}/hand-over",
                  expected_message="Pedido entregado al cliente", json={"pickup_code": order["pickup_code"]})

    assert handed["fulfillment_status"] == "collected"
    assert stock(api_db, market.own.variant, market.branches[0]) == before  # consumed once, at payment
    rejected(market_api, api_db, market.staff[0, "cajero"], "POST", f"/orders/{order['id']}/hand-over",
             400, "El pedido no está disponible para entrega", json={"pickup_code": order["pickup_code"]})


def test_cash_order_hand_over_charges_and_consumes_stock(market_api, api_db, market):
    add(market_api, market)
    order = call(market_api, market.customer, "POST", "/payments/cash/checkout", 201,
                 json={"pickup_branch_id": str(market.branches[0].id)})
    quantity, reserved = stock(api_db, market.own.variant, market.branches[0])

    handed = call(market_api, market.staff[0, "encargado"], "POST", f"/orders/{order['id']}/hand-over",
                  json={"pickup_code": order["pickup_code"]})

    assert handed["payment_status"] == "paid" and handed["fulfillment_status"] == "collected"
    assert stock(api_db, market.own.variant, market.branches[0]) == (quantity - 1, reserved - 1)


@pytest.mark.parametrize("days, message", [
    (-1, "La fecha de visita no puede ser anterior a hoy"),
    (15, "La fecha de visita no puede superar los 14 días"),
])
def test_reservation_visit_date_window(market_api, api_db, market, days, message):
    rejected(market_api, api_db, market.customer, "POST", "/reservations/", 400, message, json={
        "branch_id": str(market.branches[0].id),
        "visit_date": (date.today() + timedelta(days=days)).isoformat(),
        "items": [{"variant_id": str(market.own.variant.id), "quantity": 1}],
    })


@pytest.mark.parametrize("assignment", [
    "quantity = -1", "reserved_quantity = -1", "reserved_quantity = quantity + 1",
])
def test_inventory_rejects_impossible_stock(api_db, market, assignment):
    with pytest.raises(IntegrityError):
        api_db.execute(text(f"UPDATE inventory SET {assignment} WHERE variant_id = :variant"),
                       {"variant": market.own.variant.id})
        api_db.flush()
    api_db.rollback()


def test_branch_staff_never_see_customer_pickup_code(market_api, api_db, market):
    add(market_api, market)
    call(market_api, market.customer, "POST", "/payments/cash/checkout", 201,
         json={"pickup_branch_id": str(market.branches[0].id)})
    for role in ("encargado", "cajero"):
        orders = call(market_api, market.staff[0, role], "GET", "/orders/branch")
        assert len(orders) == 1 and orders[0]["pickup_code"] is None


def _visit(days=2):
    return (date.today() + timedelta(days=days)).isoformat()


def test_orders_and_sales_use_the_company_currency(market_api, api_db, market):
    add(market_api, market)
    order = call(market_api, market.customer, "POST", "/payments/cash/checkout", 201,
                 json={"pickup_branch_id": str(market.branches[0].id)})
    sale = call(market_api, market.staff[0, "cajero"], "POST", "/sales/", 201,
                json={"items": [{"variant_id": str(market.own.variant.id), "quantity": 1}]})
    assert order["currency"] == sale["currency"] == "bob"  # identities() companies default to BOB


def test_reservation_price_applies_product_discount(market_api, api_db, market):
    market.own.variant.product.discount_type = "fixed"
    market.own.variant.product.discount_value = 5
    api_db.commit()
    reservation = call(market_api, market.customer, "POST", "/reservations/", 201, json={
        "branch_id": str(market.branches[0].id), "visit_date": _visit(),
        "items": [{"variant_id": str(market.own.variant.id), "quantity": 1}],
    })
    assert float(reservation["items"][0]["unit_price"]) == 20
    assert float(reservation["total_amount"]) == 20


def test_reservation_rejects_too_many_units(market_api, api_db, market):
    rejected(market_api, api_db, market.customer, "POST", "/reservations/", 400,
             "Una reserva no puede superar las 5 prendas", json={
                 "branch_id": str(market.branches[0].id), "visit_date": _visit(),
                 "items": [{"variant_id": str(market.own.variant.id), "quantity": 6}],
             })


def test_customer_active_reservations_are_capped(market_api, api_db, market):
    from app.models.inventory import Inventory

    api_db.query(Inventory).filter(Inventory.variant_id == market.own.variant.id).update({"quantity": 50})
    api_db.commit()
    body = {"branch_id": str(market.branches[0].id), "visit_date": _visit(),
            "items": [{"variant_id": str(market.own.variant.id), "quantity": 1}]}
    for _ in range(3):
        call(market_api, market.customer, "POST", "/reservations/", 201, json=body)
    rejected(market_api, api_db, market.customer, "POST", "/reservations/", 400,
             "Ya tienes 3 reservas activas; atiende o cancela una antes de crear otra", json=body)
