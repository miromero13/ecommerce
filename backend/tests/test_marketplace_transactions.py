"""CU1 marketplace regressions, prepared for parent-run PostgreSQL RED.

Catch mixed-company writes, widened staff branch access, and lost customer
history. Real routes, signed tokens and SQL business logic; only outbound push
is suppressed. No lifespan tasks, payment gateways or application dotenv reads.
"""
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import text

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_employee_authorization import headers


TABLES = (
    "tenants", "users", "branches", "products", "product_variants", "inventory",
    "inventory_movements", "carts", "cart_items", "reservations", "reservation_items",
    "orders", "order_items", "sales", "sale_items", "promotion_codes",
    "promotion_code_usages", "payment_attempts", "user_product_interactions",
    "notifications",
)


def fake_stripe(monkeypatch):
    """Online payments are Stripe only: a local fake stands in for the API (no network)."""
    import itertools
    from types import SimpleNamespace

    import stripe
    from app.core.config import settings

    ids = itertools.count(1)
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_fake")
    monkeypatch.setattr(stripe.PaymentIntent, "create",
                        lambda **kwargs: SimpleNamespace(id=f"pi_test_{next(ids)}", client_secret="secret_test"))
    monkeypatch.setattr(stripe.PaymentIntent, "retrieve",
                        lambda intent_id, **kwargs: SimpleNamespace(id=intent_id, client_secret="secret_test"))
    monkeypatch.setattr(stripe.PaymentIntent, "cancel", lambda intent_id, **kwargs: None)


def stripe_webhook(api, intent_id, cents, currency, metadata):
    """What Stripe sends on payment_intent.succeeded, processed by the real handler in a request-like session."""
    from app.core.database import get_db
    from app.services.order_service import process_stripe_event

    sessions = api.app.dependency_overrides[get_db]()
    try:
        process_stripe_event(next(sessions), {"id": f"evt_{intent_id}", "type": "payment_intent.succeeded", "data": {
            "object": {"id": intent_id, "amount": cents, "currency": currency, "metadata": metadata}}})
    finally:
        sessions.close()


def cents(amount):
    return int((Decimal(str(amount)) * 100).to_integral_value())


@pytest.fixture
def market_api(api, monkeypatch):
    from app.routes import (
        cart_routes, order_routes, payment_routes, promotion_routes,
        reservation_routes, sales_routes,
    )
    from app.services import notification_delivery

    # Keep notification persistence, deduplication and recipients real. No push
    # token can cause Firebase/network access, even if fixture data later grows.
    monkeypatch.setattr(notification_delivery, "_send_push", lambda *args: None)
    fake_stripe(monkeypatch)
    for module in (cart_routes, order_routes, payment_routes, promotion_routes,
                   reservation_routes, sales_routes):
        api.app.include_router(module.router, prefix="/api")
    # conftest's api closes the client/clears overrides; each request owns a
    # separate savepoint Session. api_db's outer rollback cleans ALL commits,
    # including notifications. No background expiry/lifespan thread is started.
    return api


@pytest.fixture
def market(api_db, catalog):
    from app.models.user import User
    from app.schemas.enums import GenderEnum, RolEnum

    customer = catalog.user
    customer.rol = RolEnum.cliente
    customer.tenant_id = None
    customer.branch_id = None
    other = User(name="Other customer", email="other-customer@example.com",
                 hashed_password="unused", gender=GenderEnum.femenino,
                 rol=RolEnum.cliente, tenant_id=None, is_active=True)
    api_db.add(other)
    staff = {}
    for index, branch in enumerate(catalog.branches):
        for role in (RolEnum.administrador, RolEnum.encargado, RolEnum.cajero):
            employee = User(name=role.value, email=f"{role.value}-{index}@example.com",
                            hashed_password="unused", gender=GenderEnum.femenino,
                            rol=role, tenant_id=branch.tenant_id,
                            branch_id=branch.id, is_active=True)
            api_db.add(employee)
            staff[index, role.value] = employee
    api_db.flush()
    # 1P-CU18: till sales need the cashier's open drawer; every cashier starts the day with one.
    from app.models.cash_session import CashSession
    for (index, role), employee in staff.items():
        if role == "cajero":
            api_db.add(CashSession(tenant_id=employee.tenant_id, branch_id=employee.branch_id,
                                   cashier_id=employee.id, status="open", opening_amount=100))
    api_db.commit()
    return SimpleNamespace(customer=customer, other=other, staff=staff,
                           own=catalog.own, foreign=catalog.foreign,
                           branches=catalog.branches)


def snapshot(db):
    # Includes every stock/movement/order/reservation row, coupon usage and
    # tenant counters; read SQL rather than a potentially stale identity map.
    return {table: db.execute(text(
        f"SELECT row_to_json(t)::text FROM {table} t ORDER BY id"
    )).all() for table in TABLES}


def call(api, user, method, path, code=200, expected_message=None, **kwargs):
    result = api.request(method, "/api" + path, headers=headers(user), **kwargs)
    assert result.status_code == code, result.text
    body = result.json()
    assert body["statusCode"] == code
    if expected_message is not None:
        assert body["message"] == expected_message
    return body["data"]


def rejected(api, db, user, method, path, code=400, message=None, **kwargs):
    before = snapshot(db)
    result = api.request(method, "/api" + path, headers=headers(user), **kwargs)
    assert result.status_code == code, result.text
    body = result.json()
    if message is None:
        # New tenant-mismatch errors have no established literal contract yet.
        assert isinstance(body["message"], str) and body["message"]
        message = body["message"]
    assert body == {"statusCode": code, "message": message, "error": "HTTPException"}
    assert snapshot(db) == before


def add(api, market, group=None, branch=None):
    group = group or market.own
    branch = branch or market.branches[0]
    return call(api, market.customer, "POST", "/cart/items", 201, json={
        "variant_id": str(group.variant.id), "branch_id": str(branch.id), "quantity": 1,
    })


def reserve(api, market, group=None, branch=None):
    group = group or market.own
    branch = branch or market.branches[0]
    reservation = call(api, market.customer, "POST", "/reservations/", 201, json={
        "branch_id": str(branch.id), "visit_date": (date.today() + timedelta(days=2)).isoformat(),
        "items": [{"variant_id": str(group.variant.id), "quantity": 1}],
    })
    # D1: the reservation holds the visit once its 50 % deposit is paid online (Stripe).
    pay_deposit(api, market, reservation)
    return call(api, market.customer, "GET", f"/reservations/{reservation['id']}")


def checkout(api, market, branch=None, **extra):
    """Web order: always paid online with Stripe. Returns the pending order and its PaymentIntent id."""
    branch = branch or market.branches[0]
    started = call(api, market.customer, "POST", "/payments/stripe/checkout", 201,
                   json={"pickup_branch_id": str(branch.id), **extra})
    order = call(api, market.customer, "GET", f"/orders/{started['order_id']}")
    return {**order, "payment_intent_id": started["payment_intent_id"]}


def pay(api, market, order):
    """Stripe confirms the card payment (the webhook consumes the stock)."""
    stripe_webhook(api, order["payment_intent_id"], cents(order["total_amount"]), order["currency"],
                   {"order_id": order["id"]})


def pay_deposit(api, market, reservation):
    """The 50 % reservation deposit paid by card (Stripe)."""
    started = call(api, market.customer, "POST", f"/payments/stripe/reservations/{reservation['id']}")
    stripe_webhook(api, started["payment_intent_id"], cents(reservation["deposit_amount"]), "bob",
                   {"reservation_id": reservation["id"]})


def purchase_pending(api, market, group=None, index=0):
    reservation = reserve(api, market, group, market.branches[index])
    manager = market.staff[index, "encargado"]
    for action, status in (("arrival", "confirmed"), ("attend", "attended")):
        result = call(api, manager, "PATCH", f"/reservations/{reservation['id']}/{action}")
        assert result["status"] == status
    result = call(api, market.customer, "PATCH", f"/reservations/{reservation['id']}/decision",
                  json={"purchase": True})
    assert result["status"] == "purchase_pending"
    return result


def stock(db, variant, branch):
    return tuple(db.execute(text(
        "SELECT quantity, reserved_quantity FROM inventory "
        "WHERE variant_id = :variant AND branch_id = :branch"
    ), {"variant": variant.id, "branch": branch.id}).one())


def assert_tenant(db, table, row_id, tenant):
    assert db.execute(text(f"SELECT tenant_id FROM {table} WHERE id = :id"),
                      {"id": row_id}).scalar_one() == tenant.id


def test_empty_global_cart_is_real_customer_owned_and_can_switch_company_after_clear(market_api, api_db, market):
    cart = call(market_api, market.customer, "GET", "/cart/current")
    assert cart["user_id"] == str(market.customer.id)
    assert cart["items"] == [] and cart["item_count"] == 0
    assert Decimal(cart["total_amount"]) == 0
    # Existing public contract requires a real UUID, not a fabricated empty id.
    assert api_db.execute(text("SELECT user_id FROM carts WHERE id = :id"),
                          {"id": cart["id"]}).scalar_one() == market.customer.id
    for group, branch in ((market.own, market.branches[0]), (market.foreign, market.branches[2])):
        cart = add(market_api, market, group, branch)
        assert cart["item_count"] == 1 and Decimal(cart["total_amount"]) == 25
        assert [item["variant_id"] for item in cart["items"]] == [str(group.variant.id)]
        assert_tenant(api_db, "carts", cart["id"], group.tenant)
        cleared = call(market_api, market.customer, "DELETE", "/cart/current")
        assert cleared["items"] == [] and Decimal(cleared["total_amount"]) == 0
    assert stock(api_db, market.own.variant, market.branches[0]) == (9, 2)
    assert stock(api_db, market.foreign.variant, market.branches[2]) == (9, 2)


@pytest.mark.parametrize("case", ["mixed_items", "foreign_branch"])
def test_cart_rejects_company_mixing_without_side_effects(market_api, api_db, market, case):
    add(market_api, market)
    group = market.foreign if case == "mixed_items" else market.own
    rejected(market_api, api_db, market.customer, "POST", "/cart/items", json={
        "variant_id": str(group.variant.id), "branch_id": str(market.branches[2].id), "quantity": 1,
    })


def test_customer_cannot_update_another_customers_cart_item(market_api, api_db, market):
    cart = add(market_api, market)
    call(market_api, market.other, "GET", "/cart/current")
    rejected(market_api, api_db, market.other, "PATCH", f"/cart/items/{cart['items'][0]['id']}",
             message="Item de carrito no encontrado", json={"quantity": 2})


def test_customer_online_purchases_both_companies_keep_own_history(market_api, api_db, market):
    ids = set()
    for group, index in ((market.own, 0), (market.foreign, 2)):
        add(market_api, market, group, market.branches[index])
        order = checkout(market_api, market, market.branches[index])
        ids.add(order["id"])
        assert order["pickup_branch_id"] == str(market.branches[index].id)
        assert order["user_id"] == str(market.customer.id)
        assert order["payment_method"] == "stripe" and order["payment_status"] == "pending"
        assert Decimal(order["total_amount"]) == 25
        assert [item["variant_id"] for item in order["items"]] == [str(group.variant.id)]
        assert_tenant(api_db, "orders", order["id"], group.tenant)
        assert stock(api_db, group.variant, market.branches[index]) == (9, 3)
        pay(market_api, market, order)
        assert stock(api_db, group.variant, market.branches[index]) == (8, 2)
        collected = call(market_api, market.staff[index, "cajero"], "POST",
                         f"/orders/{order['id']}/hand-over", json={"pickup_code": order["pickup_code"]})
        assert collected["payment_status"] == "paid" and collected["fulfillment_status"] == "collected"
        movements = api_db.execute(text(
            "SELECT tenant_id, branch_id, quantity, movement_type FROM inventory_movements WHERE variant_id = :id"
        ), {"id": group.variant.id}).all()
        assert [tuple(row) for row in movements] == [(group.tenant.id, market.branches[index].id, 1, "outcome")]
        assert call(market_api, market.customer, "GET", f"/orders/{order['id']}")["id"] == order["id"]
        rejected(market_api, api_db, market.other, "GET", f"/orders/{order['id']}", 404,
                 f"Pedido con id {order['id']} no encontrado")
    assert {row["id"] for row in call(market_api, market.customer, "GET", "/orders/me")} == ids
    assert call(market_api, market.other, "GET", "/orders/me") == []


def test_checkout_rejects_other_company_pickup_without_reserving_stock(market_api, api_db, market):
    add(market_api, market)
    rejected(market_api, api_db, market.customer, "POST", "/payments/stripe/checkout",
             json={"pickup_branch_id": str(market.branches[2].id)})


def test_customer_reservations_span_companies_but_history_is_private(market_api, api_db, market):
    ids = set()
    for group, index in ((market.own, 0), (market.foreign, 2)):
        reservation = reserve(market_api, market, group, market.branches[index])
        ids.add(reservation["id"])
        assert reservation["branch_id"] == str(market.branches[index].id)
        assert reservation["user_id"] == str(market.customer.id)
        assert reservation["status"] == "pending" and Decimal(reservation["total_amount"]) == 25
        assert [item["variant_id"] for item in reservation["items"]] == [str(group.variant.id)]
        assert_tenant(api_db, "reservations", reservation["id"], group.tenant)
        assert stock(api_db, group.variant, market.branches[index]) == (9, 3)
        assert call(market_api, market.customer, "GET", f"/reservations/{reservation['id']}")["id"] == reservation["id"]
        rejected(market_api, api_db, market.other, "GET", f"/reservations/{reservation['id']}", 404,
                 f"Reserva con id {reservation['id']} no encontrada")
    assert {row["id"] for row in call(market_api, market.customer, "GET", "/reservations/me")} == ids
    assert call(market_api, market.other, "GET", "/reservations/me") == []


def test_reservation_rejects_mixed_products_atomically(market_api, api_db, market):
    rejected(market_api, api_db, market.customer, "POST", "/reservations/",
             message="No hay stock disponible suficiente para la reserva", json={
                 "branch_id": str(market.branches[0].id),
                 "visit_date": (date.today() + timedelta(days=2)).isoformat(),
                 "items": [{"variant_id": str(group.variant.id), "quantity": 1}
                           for group in (market.own, market.foreign)],
             })


@pytest.mark.parametrize("index", [0, 2])
def test_reservation_transfer_creates_company_cart_without_customer_tenant(market_api, api_db, market, index):
    group = market.own if index == 0 else market.foreign
    reservation = purchase_pending(market_api, market, group, index)
    cart = call(market_api, market.customer, "POST", f"/reservations/{reservation['id']}/to-cart")
    assert cart["user_id"] == str(market.customer.id)
    assert cart["item_count"] == 1 and Decimal(cart["total_amount"]) == 25
    assert [item["variant_id"] for item in cart["items"]] == [str(group.variant.id)]
    assert_tenant(api_db, "carts", cart["id"], group.tenant)
    assert stock(api_db, group.variant, market.branches[index]) == (9, 3)
    # Repeating an existing transfer is idempotent, never doubles lines/holds.
    before = snapshot(api_db)
    repeated = call(market_api, market.customer, "POST", f"/reservations/{reservation['id']}/to-cart")
    assert repeated == cart
    assert snapshot(api_db) == before


def test_reservation_transfer_cannot_mix_company_with_existing_cart(market_api, api_db, market):
    reservation = purchase_pending(market_api, market, market.foreign, 2)
    add(market_api, market)
    rejected(market_api, api_db, market.customer, "POST", f"/reservations/{reservation['id']}/to-cart")


def test_cart_cannot_attach_other_company_reservation_to_own_variant(market_api, api_db, market):
    reservation = purchase_pending(market_api, market, market.foreign, 2)
    add(market_api, market)
    rejected(market_api, api_db, market.customer, "POST", "/cart/items", json={
        "variant_id": str(market.own.variant.id), "branch_id": str(market.branches[0].id),
        "reservation_id": reservation["id"], "quantity": 1,
    })


def test_reserved_online_purchase_consumes_hold_once_and_closes_reservation(market_api, api_db, market):
    reservation = purchase_pending(market_api, market)
    call(market_api, market.customer, "POST", f"/reservations/{reservation['id']}/to-cart")
    order = checkout(market_api, market)
    # Checkout must reuse the reservation hold, not reserve a second unit.
    assert stock(api_db, market.own.variant, market.branches[0]) == (9, 3)
    pay(market_api, market, order)
    collected = call(market_api, market.staff[0, "cajero"], "POST",
                     f"/orders/{order['id']}/hand-over", json={"pickup_code": order["pickup_code"]})
    assert collected["payment_status"] == "paid"
    assert stock(api_db, market.own.variant, market.branches[0]) == (8, 2)
    closed = call(market_api, market.customer, "GET", f"/reservations/{reservation['id']}")
    assert closed["status"] == "sold" and closed["cart_id"] is None
    rejected(market_api, api_db, market.customer, "POST", f"/reservations/{reservation['id']}/to-cart",
             message="Solo una reserva pendiente de compra puede pasar al carrito")


@pytest.mark.parametrize("action", ["arrival", "attend", "branch-cancel"])
@pytest.mark.parametrize("staff_index", [1, 2])
def test_reservation_staff_cannot_override_assigned_branch(market_api, api_db, market, action, staff_index):
    reservation = reserve(market_api, market)
    if action == "attend":
        call(market_api, market.staff[0, "encargado"], "PATCH", f"/reservations/{reservation['id']}/arrival")
    rejected(market_api, api_db, market.staff[staff_index, "encargado"], "PATCH",
             f"/reservations/{reservation['id']}/{action}", 403,
             "No tienes permisos para esta sucursal", params={"branch_id": str(market.branches[0].id)})


def test_company_admin_cannot_list_other_company_reservations(market_api, api_db, market):
    reserve(market_api, market, market.foreign, market.branches[2])
    rejected(market_api, api_db, market.staff[0, "administrador"], "GET", "/reservations/branch", 404,
             f"Sucursal con id {market.branches[2].id} no encontrada",
             params={"branch_id": str(market.branches[2].id)})


@pytest.mark.parametrize("index", [1, 2])
def test_hand_over_retains_company_and_assigned_branch_scope(market_api, api_db, market, index):
    add(market_api, market)
    order = checkout(market_api, market)
    pay(market_api, market, order)
    rejected(market_api, api_db, market.staff[index, "cajero"], "POST",
             f"/orders/{order['id']}/hand-over", message="Pedido no encontrado",
             json={"pickup_code": order["pickup_code"]})
    assert call(market_api, market.staff[index, "encargado"], "GET", "/orders/branch") == []
    rejected(market_api, api_db, market.staff[index, "encargado"], "POST",
             f"/orders/{order['id']}/ready", 404, "Pedido no encontrado en tu sucursal")


def test_own_company_direct_cash_sale_preserves_stock_movement_and_receipt(market_api, api_db, market):
    cashier = market.staff[0, "cajero"]
    sale = call(market_api, cashier, "POST", "/sales/", 201,
                json={"items": [{"variant_id": str(market.own.variant.id), "quantity": 1}]})
    assert sale["branch_id"] == str(market.branches[0].id)
    assert sale["payment_method"] == "cash" and sale["payment_status"] == "paid"
    assert Decimal(sale["total_amount"]) == 25
    assert [item["variant_id"] for item in sale["items"]] == [str(market.own.variant.id)]
    assert_tenant(api_db, "sales", sale["id"], market.own.tenant)
    assert stock(api_db, market.own.variant, market.branches[0]) == (8, 2)
    assert stock(api_db, market.foreign.variant, market.branches[2]) == (9, 2)
    movements = api_db.execute(text(
        "SELECT tenant_id, branch_id, quantity, movement_type FROM inventory_movements"
    )).all()
    assert [tuple(row) for row in movements] == [(market.own.tenant.id, market.branches[0].id, 1, "outcome")]
    assert call(market_api, cashier, "GET", f"/sales/{sale['id']}")["id"] == sale["id"]
    rejected(market_api, api_db, market.staff[2, "administrador"], "GET", f"/sales/{sale['id']}",
             404, f"Venta con id {sale['id']} no encontrada")


@pytest.mark.parametrize("case", ["foreign_variant", "foreign_branch"])
def test_pos_rejects_foreign_company_without_sale_or_stock_changes(market_api, api_db, market, case):
    payload = {"items": [{"variant_id": str(market.own.variant.id), "quantity": 1}]}
    if case == "foreign_branch":
        payload["branch_id"] = str(market.branches[2].id)
        code, message = 403, "No tienes permisos para esta sucursal"
    else:
        payload["items"].append({"variant_id": str(market.foreign.variant.id), "quantity": 1})
        code, message = 400, "No existe inventario para la variante seleccionada"
    rejected(market_api, api_db, market.staff[0, "cajero"], "POST", "/sales/", code, message, json=payload)


@pytest.fixture
def coupons(api_db, market):
    from app.models.promotion_code import PromotionCode
    codes = []
    for group, index in ((market.own, 0), (market.foreign, 2)):
        code = PromotionCode(tenant_id=group.tenant.id, code=f"TENANT-{index}",
                             discount_type="fixed", discount_value=5,
                             created_by=market.staff[index, "administrador"].id)
        api_db.add(code)
        codes.append(code)
    api_db.commit()
    return codes


def test_foreign_company_coupon_is_rejected_without_usage_or_cart_changes(market_api, api_db, market, coupons):
    add(market_api, market)
    rejected(market_api, api_db, market.customer, "POST", "/cart/coupon", json={"code": coupons[1].code})


def lifecycle_ledger(db):
    # Transfers/clear may change transient cart links, never economic/history rows.
    return {table: rows for table, rows in snapshot(db).items()
            if table not in {"carts", "cart_items", "reservations", "notifications"}}


def assert_lifecycle_cart(db, cart, market, group, cart_id):
    assert cart["id"] == cart_id and cart["user_id"] == str(market.customer.id)
    assert cart["status"] == "active" and cart["item_count"] == 1
    assert [(item["variant_id"], item["quantity"]) for item in cart["items"]] == [(str(group.variant.id), 1)]
    assert Decimal(cart["total_amount"]) == 25 and Decimal(cart["discount_amount"]) == 0
    assert_tenant(db, "carts", cart_id, group.tenant)


def test_reserved_lifecycle_clear_rebuilds_same_reservation_once(market_api, api_db, market):
    reservation = purchase_pending(market_api, market)
    path = f"/reservations/{reservation['id']}/to-cart"
    cart = call(market_api, market.customer, "POST", path)
    before = lifecycle_ledger(api_db)
    cleared = call(market_api, market.customer, "DELETE", "/cart/current",
                   expected_message="Carrito vaciado exitosamente")
    assert cleared["id"] == cart["id"] and cleared["items"] == []
    assert cleared["item_count"] == 0 and Decimal(cleared["total_amount"]) == 0
    assert api_db.execute(text("SELECT tenant_id FROM carts WHERE id = :id"), {"id": cart["id"]}).scalar_one() is None
    kept = call(market_api, market.customer, "GET", f"/reservations/{reservation['id']}")
    assert kept["status"] == "purchase_pending" and kept["items"] == reservation["items"]
    rebuilt = call(market_api, market.customer, "POST", path,
                   expected_message="Reserva transferida al carrito")
    assert_lifecycle_cart(api_db, rebuilt, market, market.own, cart["id"])
    assert stock(api_db, market.own.variant, market.branches[0]) == (9, 3)
    assert stock(api_db, market.foreign.variant, market.branches[2]) == (9, 2)
    assert lifecycle_ledger(api_db) == before
    stable = snapshot(api_db)
    assert call(market_api, market.customer, "POST", path) == rebuilt
    history = call(market_api, market.customer, "GET", "/reservations/me")
    assert [(row["id"], row["status"], row["cart_id"]) for row in history] == [
        (reservation["id"], "purchase_pending", cart["id"])]
    assert snapshot(api_db) == stable


def test_reserved_lifecycle_clear_allows_other_company_transfer(market_api, api_db, market):
    first = purchase_pending(market_api, market)
    second = purchase_pending(market_api, market, market.foreign, 2)
    cart = call(market_api, market.customer, "POST", f"/reservations/{first['id']}/to-cart")
    before = lifecycle_ledger(api_db)
    cleared = call(market_api, market.customer, "DELETE", "/cart/current",
                   expected_message="Carrito vaciado exitosamente")
    assert cleared["id"] == cart["id"] and cleared["items"] == []
    switched = call(market_api, market.customer, "POST", f"/reservations/{second['id']}/to-cart",
                    expected_message="Reserva transferida al carrito")
    assert_lifecycle_cart(api_db, switched, market, market.foreign, cart["id"])
    history = {row["id"]: row for row in call(market_api, market.customer, "GET", "/reservations/me")}
    assert set(history) == {first["id"], second["id"]}
    for original in (first, second):
        row = history[original["id"]]
        assert row["user_id"] == str(market.customer.id) and row["status"] == "purchase_pending"
        assert row["items"] == original["items"] and row["branch_id"] == original["branch_id"]
    assert history[first["id"]]["cart_id"] is None
    assert history[second["id"]]["cart_id"] == cart["id"]
    assert stock(api_db, market.own.variant, market.branches[0]) == (9, 3)
    assert stock(api_db, market.foreign.variant, market.branches[2]) == (9, 3)
    assert lifecycle_ledger(api_db) == before


def test_reserved_lifecycle_online_purchase_reuses_cart_across_companies(market_api, api_db, market, coupons):
    orders, reservations, cart_id = set(), set(), None
    for group, index, coupon in ((market.own, 0, coupons[0]), (market.foreign, 2, coupons[1])):
        reservation = purchase_pending(market_api, market, group, index)
        reservations.add(reservation["id"])
        cart = call(market_api, market.customer, "POST", f"/reservations/{reservation['id']}/to-cart")
        cart_id = cart_id or cart["id"]
        assert_lifecycle_cart(api_db, cart, market, group, cart_id)
        call(market_api, market.customer, "POST", "/cart/coupon", json={"code": coupon.code})
        order = checkout(market_api, market, market.branches[index])
        orders.add(order["id"])
        assert_tenant(api_db, "orders", order["id"], group.tenant)
        assert order["pickup_branch_id"] == str(market.branches[index].id)
        assert [item["variant_id"] for item in order["items"]] == [str(group.variant.id)]
        # 25 list price - 5 coupon - 12.50 paid reservation deposit (D1).
        assert Decimal(str(order["deposit_applied"])) == Decimal("12.50")
        assert Decimal(order["total_amount"]) == Decimal("7.50")
        assert stock(api_db, group.variant, market.branches[index]) == (9, 3)
        pay(market_api, market, order)
        paid = call(market_api, market.staff[index, "cajero"], "POST", f"/orders/{order['id']}/hand-over",
                    expected_message="Pedido entregado al cliente", json={"pickup_code": order["pickup_code"]})
        assert paid["status"] == "paid" and paid["fulfillment_status"] == "collected"
        assert stock(api_db, group.variant, market.branches[index]) == (8, 2)
        empty = call(market_api, market.customer, "GET", "/cart/current")
        assert empty["id"] == cart_id and empty["status"] == "active" and empty["items"] == []
        assert empty["item_count"] == 0 and Decimal(empty["total_amount"]) == 0
        assert api_db.execute(text("SELECT tenant_id FROM carts WHERE id = :id"), {"id": cart_id}).scalar_one() is None
    history = call(market_api, market.customer, "GET", "/orders/me")
    assert {row["id"] for row in history} == orders
    assert all(row["payment_status"] == "paid" and row["user_id"] == str(market.customer.id) for row in history)
    history = call(market_api, market.customer, "GET", "/reservations/me")
    assert {row["id"] for row in history} == reservations
    assert all(row["status"] == "sold" and row["cart_id"] is None for row in history)
    movements = api_db.execute(text(
        "SELECT tenant_id, branch_id, variant_id, quantity, movement_type FROM inventory_movements"
    )).all()
    assert {tuple(row) for row in movements} == {
        (market.own.tenant.id, market.branches[0].id, market.own.variant.id, 1, "outcome"),
        (market.foreign.tenant.id, market.branches[2].id, market.foreign.variant.id, 1, "outcome"),
    }
    assert len(movements) == 2
    assert stock(api_db, market.own.variant, market.branches[0]) == (8, 2)
    assert stock(api_db, market.foreign.variant, market.branches[2]) == (8, 2)
    usages = api_db.execute(text("SELECT promotion_code_id, user_id FROM promotion_code_usages")).all()
    assert {tuple(row) for row in usages} == {(coupon.id, market.customer.id) for coupon in coupons}
    assert len(usages) == 2
    assert api_db.execute(text("SELECT count(*) FROM sales")).scalar_one() == 0


def test_reserved_lifecycle_cancel_releases_hold_once_and_unlocks_cart(market_api, api_db, market, coupons):
    reservation = purchase_pending(market_api, market)
    other = reserve(market_api, market, market.foreign, market.branches[2])
    cart = call(market_api, market.customer, "POST", f"/reservations/{reservation['id']}/to-cart")
    call(market_api, market.customer, "POST", "/cart/coupon", json={"code": coupons[0].code})
    order = checkout(market_api, market)
    assert stock(api_db, market.own.variant, market.branches[0]) == (9, 3)
    # Preserve the existing manual-decision guard: only checkout cancellation
    # may close this purchase and release its hold while an order is pending.
    rejected(market_api, api_db, market.customer, "PATCH",
             f"/reservations/{reservation['id']}/decision",
             message="Transición de reserva no permitida: purchase_pending -> not_sold",
             json={"purchase": False})
    cancelled = call(market_api, market.customer, "POST", f"/orders/{order['id']}/cancel",
                     expected_message="Pedido cancelado")
    # Preserve the baseline shape: failed order/payment, cancelled fulfillment.
    assert (cancelled["status"], cancelled["payment_status"], cancelled["fulfillment_status"]) == (
        "failed", "failed", "cancelled")
    assert stock(api_db, market.own.variant, market.branches[0]) == (9, 2)
    assert stock(api_db, market.foreign.variant, market.branches[2]) == (9, 3)
    empty = call(market_api, market.customer, "GET", "/cart/current")
    assert empty["id"] == cart["id"] and empty["status"] == "active" and empty["items"] == []
    assert empty["item_count"] == 0 and Decimal(empty["total_amount"]) == 0
    assert empty["promotion_code_id"] is None
    assert api_db.execute(text("SELECT tenant_id FROM carts WHERE id = :id"), {"id": cart["id"]}).scalar_one() is None
    history = {row["id"]: row for row in call(market_api, market.customer, "GET", "/reservations/me")}
    assert set(history) == {reservation["id"], other["id"]}
    assert history[reservation["id"]]["status"] == "not_sold"
    assert history[reservation["id"]]["cart_id"] is None
    assert history[reservation["id"]]["items"] == reservation["items"]
    assert history[other["id"]] == other
    assert [row["id"] for row in call(market_api, market.customer, "GET", "/orders/me")] == [order["id"]]
    for table in ("inventory_movements", "promotion_code_usages", "sales"):
        assert api_db.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 0
    rejected(market_api, api_db, market.customer, "POST", f"/orders/{order['id']}/cancel",
             message="El pedido no se puede cancelar")
    stable = snapshot(api_db)
    assert call(market_api, market.customer, "GET", f"/orders/{order['id']}") == cancelled
    assert snapshot(api_db) == stable


def test_own_company_coupon_cash_collection_records_one_usage(market_api, api_db, market, coupons):
    add(market_api, market)
    cart = call(market_api, market.customer, "POST", "/cart/coupon", json={"code": coupons[0].code})
    assert Decimal(cart["discount_amount"]) == 5 and Decimal(cart["total_amount"]) == 20
    order = checkout(market_api, market)
    assert Decimal(order["total_amount"]) == 20
    pay(market_api, market, order)
    cashier = market.staff[0, "cajero"]
    call(market_api, cashier, "POST", f"/orders/{order['id']}/hand-over",
         json={"pickup_code": order["pickup_code"]})
    usages = api_db.execute(text("SELECT promotion_code_id, user_id FROM promotion_code_usages")).all()
    assert [tuple(row) for row in usages] == [(coupons[0].id, market.customer.id)]
    rejected(market_api, api_db, cashier, "POST", f"/orders/{order['id']}/hand-over",
             message="El pedido no está disponible para entrega", json={"pickup_code": order["pickup_code"]})


def test_pending_web_order_does_not_block_buying_from_other_company(market_api, api_db, market):
    reservation = purchase_pending(market_api, market)
    path = f"/reservations/{reservation['id']}/to-cart"
    call(market_api, market.customer, "POST", path)
    order = checkout(market_api, market)
    empty = call(market_api, market.customer, "GET", "/cart/current")
    assert empty["status"] == "active" and empty["items"] == []
    # A pending pickup order must not lock the cart for other companies.
    cart = add(market_api, market, market.foreign, market.branches[2])
    assert cart["item_count"] == 1
    call(market_api, market.customer, "DELETE", "/cart/current")
    # The reservation already travels in the pending order: no second checkout.
    rejected(market_api, api_db, market.customer, "POST", path,
             message="La reserva ya tiene un pedido pendiente de pago")
    add(market_api, market, market.foreign, market.branches[2])
    # Paying the first order must not wipe the new company's cart.
    pay(market_api, market, order)
    cart = call(market_api, market.customer, "GET", "/cart/current")
    assert [item["variant_id"] for item in cart["items"]] == [str(market.foreign.variant.id)]
    assert_tenant(api_db, "carts", cart["id"], market.foreign.tenant)
    assert stock(api_db, market.own.variant, market.branches[0]) == (8, 2)
