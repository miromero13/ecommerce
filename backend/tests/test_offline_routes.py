"""CU25/CU30: offline cash sales. The first sale to reach the server keeps the last unit; the other
becomes a persisted conflict whose cash is held in the drawer until a person resolves it once.
Shared fixtures: every cashier has an open drawer of 100 Bs.; the own variant costs 25 Bs."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_employee_authorization import headers
from test_marketplace_transactions import call, market, market_api  # noqa: F401


@pytest.fixture
def offline_api(market_api):
    from app.routes import cash_session_routes, offline_routes

    market_api.app.include_router(cash_session_routes.router, prefix="/api")
    market_api.app.include_router(offline_routes.router, prefix="/api")
    return market_api


@pytest.fixture
def till(api_db, market):
    """Branch 0 with ONE unit left and two cashiers (two devices), each with an open 100 Bs. drawer."""
    from app.models.cash_session import CashSession
    from app.models.user import User
    from app.schemas.enums import GenderEnum, RolEnum

    first = market.staff[0, "cajero"]
    second = User(name="Cajero 2", email="offline-device-b@example.com", hashed_password="unused",
                  gender=GenderEnum.femenino, rol=RolEnum.cajero, tenant_id=first.tenant_id,
                  branch_id=first.branch_id, is_active=True)
    api_db.add(second)
    api_db.flush()
    api_db.add(CashSession(tenant_id=second.tenant_id, branch_id=second.branch_id,
                           cashier_id=second.id, status="open", opening_amount=100))
    market.own.inventory.quantity = 3  # reserved 2 -> exactly 1 available
    api_db.commit()
    return first, second


def sale_op(market, minutes_ago=5, **extra):
    op = {
        "operation_id": str(uuid4()), "receipt_number": f"CONT-20261110-{uuid4().int % 9000 + 1000}",
        "type": "cash_sale",
        "created_at": (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat(),
        "branch_id": str(market.branches[0].id), "customer_name": "Ana Pérez", "customer_phone": "70000000",
        "customer_email": market.customer.email,
        "items": [{"variant_id": str(market.own.variant.id), "quantity": 1, "unit_price": "25.00"}],
        "subtotal": "25.00", "discount": "0", "total": "25.00", "cash_received": "50.00", "change_returned": "25.00",
    }
    op.update(extra)
    return op


def sync(api, cashier, *ops):
    return call(api, cashier, "POST", "/offline/queue-sync", json={"operations": list(ops)})


def drawer(api, cashier):
    return call(api, cashier, "GET", "/cash-sessions/current")


def money(value):
    return Decimal(str(value))


def stock(api_db, market):
    return api_db.execute(text("SELECT quantity FROM inventory WHERE id = :id"),
                          {"id": market.own.inventory.id}).scalar()


def count(api_db, sql, **params):
    return api_db.execute(text(sql), params).scalar()


@pytest.fixture
def conflict(offline_api, market, till):
    """Both devices sold the last unit offline; A sold earlier (and syncs first) and keeps it."""
    first, second = till
    won, lost = sale_op(market, minutes_ago=10), sale_op(market, minutes_ago=3)
    assert sync(offline_api, first, won)["synced_ids"] == [won["operation_id"]]
    result = sync(offline_api, second, lost)
    assert result["synced_ids"] == [] and result["conflicts_count"] == 1
    return result["conflicts"][0], won, lost


def test_last_unit_goes_to_the_earliest_sale_and_the_other_is_held_not_lost(offline_api, api_db, market, till, conflict):
    first, second = till
    data, won, lost = conflict
    assert data["status"] == "pending" and data["operation_id"] == lost["operation_id"]
    assert data["reason"].startswith("Sin stock para SKU SKU-0-active: disponible 0, requerido 1")
    assert (data["customer_name"], data["customer_phone"]) == ("Ana Pérez", "70000000")
    assert stock(api_db, market) == 2  # one unit sold, reserved units untouched

    # Device A: a normal cash sale in its drawer. Device B: the cash is held, never lost.
    a, b = drawer(offline_api, first), drawer(offline_api, second)
    assert (money(a["cash_sales"]), money(a["expected_amount"])) == (Decimal("25.00"), Decimal("125.00"))
    assert (money(b["cash_sales"]), money(b["held"]), money(b["expected_amount"])) == (Decimal("0.00"), Decimal("25.00"), Decimal("125.00"))

    listed = call(offline_api, market.staff[0, "administrador"], "GET", "/offline/conflicts")
    assert (listed["pending_count"], money(listed["pending_total"])) == (1, Decimal("25.00"))

    # Re-sending both batches (e.g. the response was lost) never duplicates a sale or a conflict.
    assert sync(offline_api, first, won)["synced_ids"] == [won["operation_id"]]
    assert sync(offline_api, second, lost)["conflicts"][0]["id"] == data["id"]
    assert count(api_db, "SELECT count(*) FROM sales WHERE offline_operation_id IS NOT NULL") == 1
    assert count(api_db, "SELECT count(*) FROM offline_sale_conflicts") == 1
    assert stock(api_db, market) == 2


def test_an_online_sale_that_arrives_first_beats_the_offline_one(offline_api, market, till):
    first, second = till
    call(offline_api, first, "POST", "/sales/", 201,
         json={"items": [{"variant_id": str(market.own.variant.id), "quantity": 1}]})
    result = sync(offline_api, second, sale_op(market))
    assert result["synced_count"] == 0 and result["conflicts"][0]["reason"].startswith("Sin stock")


def test_cash_refund_leaves_the_drawer_balanced_and_happens_once(offline_api, market, till, conflict):
    _, second = till
    data, _, _ = conflict
    resolved = call(offline_api, second, "POST", f"/offline/conflicts/{data['id']}/resolve",
                    expected_message="Conflicto resuelto: efectivo devuelto al cliente y registrado como retiro de caja.",
                    json={"action": "cash_refund"})
    assert (resolved["status"], resolved["resolution"], money(resolved["refund_amount"])) == ("resolved", "cash_refund", Decimal("25.00"))
    assert resolved["refund_receipt_number"] == f"DEV-{data['receipt_number']}"
    b = drawer(offline_api, second)
    assert (money(b["held"]), money(b["withdrawals"]), money(b["expected_amount"])) == (Decimal("25.00"), Decimal("25.00"), Decimal("100.00"))

    again = offline_api.post(f"/api/offline/conflicts/{data['id']}/resolve", json={"action": "cash_refund"},
                             headers=headers(second))
    assert again.status_code == 409 and again.json()["message"] == "Este conflicto ya fue resuelto"
    assert money(drawer(offline_api, second)["withdrawals"]) == Decimal("25.00")


def test_cash_refund_needs_an_open_drawer_with_enough_cash(offline_api, api_db, market, till, conflict):
    data, _, _ = conflict
    admin = market.staff[0, "administrador"]  # admins have no drawer
    result = offline_api.post(f"/api/offline/conflicts/{data['id']}/resolve", json={"action": "cash_refund"},
                              headers=headers(admin))
    assert result.status_code == 400 and result.json()["message"] == "Abre tu caja para mover efectivo en esta resolución"

    _, second = till
    api_db.execute(text("UPDATE cash_sessions SET opening_amount = 0 WHERE cashier_id = :id"), {"id": second.id})
    api_db.execute(text("INSERT INTO cash_movements (id, session_id, type, method, amount, reason) "
                        "SELECT gen_random_uuid(), id, 'withdrawal', 'cash', 20, 'Depósito' FROM cash_sessions WHERE cashier_id = :id"),
                   {"id": second.id})
    api_db.commit()
    result = offline_api.post(f"/api/offline/conflicts/{data['id']}/resolve", json={"action": "cash_refund"},
                              headers=headers(second))
    assert result.json()["message"] == "No hay efectivo suficiente en caja para devolver 25.00 Bs. (la caja tiene 5.00 Bs.)"
    assert call(offline_api, second, "GET", "/offline/conflicts")["pending_count"] == 1


def test_wallet_credit_gives_110_percent_to_the_registered_customer(offline_api, api_db, market, till, conflict):
    _, second = till
    data, _, _ = conflict
    unknown = offline_api.post(f"/api/offline/conflicts/{data['id']}/resolve",
                               json={"action": "wallet_credit", "customer_email": "nobody@example.com"},
                               headers=headers(second))
    assert unknown.status_code == 404
    resolved = call(offline_api, second, "POST", f"/offline/conflicts/{data['id']}/resolve",
                    json={"action": "wallet_credit"})  # falls back to the email taken at the till
    assert money(resolved["wallet_credit_amount"]) == Decimal("27.50")
    balance = count(api_db, "SELECT w.balance FROM user_wallets w WHERE w.user_id = :id", id=market.customer.id)
    assert balance == Decimal("27.50")
    # The cash stays in the drawer: the company keeps it and owes the customer store credit.
    assert money(drawer(offline_api, second)["expected_amount"]) == Decimal("125.00")


def test_delivered_keeps_the_sale_and_records_the_inventory_adjustment(offline_api, api_db, market, till, conflict):
    _, second = till
    data, _, lost = conflict
    resolved = call(offline_api, second, "POST", f"/offline/conflicts/{data['id']}/resolve", json={"action": "delivered"})
    assert resolved["sale_id"]
    assert count(api_db, "SELECT total_amount FROM sales WHERE offline_operation_id = :op", op=lost["operation_id"]) == Decimal("25.00")
    assert stock(api_db, market) == 2  # +1 unit found, -1 unit sold
    notes = [row[0] for row in api_db.execute(text(
        "SELECT movement_type || ':' || note FROM inventory_movements WHERE note LIKE :n ORDER BY movement_type"),
        {"n": f"%{data['receipt_number']}%"})]
    assert notes == [f"income:Ajuste: unidad física no registrada (conflicto offline {data['receipt_number']})",
                     f"outcome:Venta offline entregada {data['receipt_number']}"]


def test_exchange_for_a_pricier_garment_charges_the_difference(offline_api, api_db, market, till, conflict):
    from app.models.inventory import Inventory
    from app.models.product_variant import ProductVariant
    from app.schemas.catalog_enums import ProductStatusEnum

    _, second = till
    data, _, _ = conflict
    other = ProductVariant(tenant_id=market.own.variant.tenant_id, product_id=market.own.variant.product_id,
                           sku="SKU-0-L", price=40, size_id=api_db.execute(text("SELECT id FROM sizes WHERE name = 'L'")).scalar(),
                           color_id=market.own.variant.color_id, status=ProductStatusEnum.active)
    api_db.add(other)
    api_db.flush()
    api_db.add(Inventory(tenant_id=other.tenant_id, variant_id=other.id, branch_id=market.branches[0].id,
                         quantity=4, reserved_quantity=0, minimum_stock=0))
    api_db.commit()
    body = {"action": "exchange", "exchange_items": [{"variant_id": str(other.id), "quantity": 1}]}
    short = offline_api.post(f"/api/offline/conflicts/{data['id']}/resolve", json={**body, "cash_received": "10"},
                             headers=headers(second))
    assert short.status_code == 400 and short.json()["message"] == "El cliente debe pagar la diferencia de 15.00 Bs."

    resolved = call(offline_api, second, "POST", f"/offline/conflicts/{data['id']}/resolve", json={**body, "cash_received": "20"})
    assert money(resolved["extra_charged"]) == Decimal("15.00")
    assert count(api_db, "SELECT quantity FROM inventory WHERE variant_id = :v", v=other.id) == 3
    b = drawer(offline_api, second)
    assert (money(b["cash_sales"]), money(b["held"]), money(b["expected_amount"])) == (Decimal("15.00"), Decimal("25.00"), Decimal("140.00"))


def test_sync_needs_a_cashier_and_only_accepts_the_own_branch(offline_api, api_db, market, till):
    first, _ = till
    assert offline_api.post("/api/offline/queue-sync", json={"operations": []}).status_code == 403  # no token
    assert offline_api.post("/api/offline/queue-sync", json={"operations": []},
                            headers=headers(market.customer)).status_code == 403
    foreign = sale_op(market, branch_id=str(market.branches[1].id))
    result = sync(offline_api, first, foreign)
    assert result["rejected"] == [{"operation_id": foreign["operation_id"], "reason": "La venta pertenece a otra sucursal"}]
    assert count(api_db, "SELECT count(*) FROM sales") == 0


def test_inconsistent_amounts_are_kept_as_a_conflict(offline_api, market, till):
    first, _ = till
    result = sync(offline_api, first, sale_op(market, total="20.00", cash_received="20.00"))
    assert result["conflicts"][0]["reason"] == "Montos inconsistentes: total 20.00 Bs. y suma de prendas 25.00 Bs."


# ---------------------------------------------------------------- offline queue by time

def ago(minutes):
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()


def test_an_earlier_sale_that_syncs_later_takes_the_unit_back(offline_api, api_db, market, till):
    first, second = till
    early, late = sale_op(market, minutes_ago=10), sale_op(market, minutes_ago=3)
    assert sync(offline_api, second, late)["synced_ids"] == [late["operation_id"]]  # B reconnects first
    result = sync(offline_api, first, early)  # A charged first: A keeps the garment
    assert result["synced_ids"] == [early["operation_id"]] and result["conflicts_count"] == 0

    displaced = call(offline_api, second, "GET", "/offline/conflicts")["items"]
    assert [c["operation_id"] for c in displaced] == [late["operation_id"]]
    assert displaced[0]["reason"].startswith(f"Desplazada: la operación offline {early['receipt_number']} se hizo antes")
    assert displaced[0]["customer_phone"] == "70000000"
    assert stock(api_db, market) == 2  # still exactly one unit sold
    assert count(api_db, "SELECT count(*) FROM sales WHERE status = 'completed'") == 1
    # B's cash did not vanish: it moved from 'sale' to 'held' in the same drawer.
    b = drawer(offline_api, second)
    assert (money(b["cash_sales"]), money(b["held"]), money(b["expected_amount"])) == (Decimal("0.00"), Decimal("25.00"), Decimal("125.00"))
    assert money(drawer(offline_api, first)["cash_sales"]) == Decimal("25.00")
    # B's conflict resolves like any other (its operation id was freed for the new sale).
    call(offline_api, second, "POST", f"/offline/conflicts/{displaced[0]['id']}/resolve", json={"action": "delivered"})


def test_a_device_time_out_of_range_gets_no_priority(offline_api, market, till):
    first, second = till
    sync(offline_api, second, sale_op(market, minutes_ago=3))
    result = sync(offline_api, first, sale_op(market, minutes_ago=60 * 24 * 3))  # "three days ago"
    assert result["conflicts_count"] == 1 and result["synced_count"] == 0


def offline_add(api, market, minutes_ago):
    """The phone sends the garment it saved without internet, with the time it was added."""
    return call(api, market.customer, "POST", "/cart/items", 201, json={
        "variant_id": str(market.own.variant.id), "branch_id": str(market.branches[0].id), "quantity": 1,
        "offline_requested_at": ago(minutes_ago)})


def test_phone_order_made_offline_first_takes_the_unit_from_a_later_till_sale(offline_api, api_db, market, till):
    from test_marketplace_transactions import checkout

    _, second = till
    sync(offline_api, second, sale_op(market, minutes_ago=3))
    offline_add(offline_api, market, 10)
    order = checkout(offline_api, market, offline_requested_at=ago(10))
    assert order["status"] == "pending"  # reserved, now the customer pays with Stripe
    assert call(offline_api, second, "GET", "/offline/conflicts")["pending_count"] == 1


def test_phone_order_made_offline_later_is_never_charged(offline_api, api_db, market, till):
    first, _ = till
    sync(offline_api, first, sale_op(market, minutes_ago=10))
    offline_add(offline_api, market, 3)
    result = offline_api.post("/api/payments/stripe/checkout", headers=headers(market.customer),
                              json={"pickup_branch_id": str(market.branches[0].id), "offline_requested_at": ago(3)})
    assert result.status_code == 400
    assert result.json()["message"] == "Otra persona compró esta prenda antes que tú. No se te cobró nada."
    assert count(api_db, "SELECT count(*) FROM orders") == 0


def test_an_earlier_till_sale_cancels_a_later_unpaid_phone_order(offline_api, api_db, market, till):
    from test_marketplace_transactions import add, checkout

    first, _ = till
    add(offline_api, market)
    order = checkout(offline_api, market, offline_requested_at=ago(3))
    result = sync(offline_api, first, sale_op(market, minutes_ago=10))
    assert result["synced_count"] == 1
    status = api_db.execute(text("SELECT status, payment_status FROM orders WHERE id = :id"), {"id": order["id"]}).one()
    assert tuple(status) == ("cancelled", "failed")
    titles = [row[0] for row in api_db.execute(text("SELECT title FROM notifications WHERE user_id = :u"),
                                               {"u": market.customer.id})]
    assert "Otra persona compró antes que tú" in titles


def test_a_phone_order_already_paid_online_is_final(offline_api, api_db, market, till):
    from test_marketplace_transactions import add, checkout, pay

    first, _ = till
    add(offline_api, market)
    pay(offline_api, market, checkout(offline_api, market, offline_requested_at=ago(3)))
    result = sync(offline_api, first, sale_op(market, minutes_ago=10))
    assert result["conflicts_count"] == 1  # paid with Stripe: never displaced
