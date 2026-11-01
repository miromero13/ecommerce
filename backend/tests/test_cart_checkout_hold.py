"""The cart keeps its items while a card order waits for payment: it empties only when the order is
paid or after 40 minutes unpaid. A failed/cancelled/displaced payment gives the same cart back."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import text

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_employee_authorization import headers
from test_marketplace_transactions import (  # noqa: F401
    add, call, checkout, market, market_api, pay, purchase_pending, rejected, stock,
)
from test_delivery import NEAR, delivery_api  # noqa: F401
from test_offline_routes import ago, offline_add, offline_api, sale_op, sync, till  # noqa: F401

LOCKED = "Tienes un pedido pendiente de pago. Págalo o cancélalo para modificar el carrito."
OTHER_BRANCH = "Tienes un pedido pendiente de pago en otra sucursal. Págalo o cancélalo primero."
OTHER_MODE = "Tienes un pedido pendiente de pago con otra modalidad de entrega. Págalo o cancélalo primero."
OTHER_ADDRESS = "Tienes un pedido pendiente de pago con otra dirección de envío. Págalo o cancélalo primero."


@pytest.fixture
def hold_api(market_api):
    from app.routes import wallet_routes

    market_api.app.include_router(wallet_routes.router, prefix="/api")
    return market_api


def in_session(api, fn):
    """Run service code in a request-like session (what the webhook / expiry loop do)."""
    from app.core.database import get_db

    sessions = api.app.dependency_overrides[get_db]()
    try:
        return fn(next(sessions))
    finally:
        sessions.close()


def stripe_event(api, intent_id, event_type):
    from app.services.order_service import process_stripe_event

    in_session(api, lambda db: process_stripe_event(db, {"id": f"evt_{event_type}_{intent_id}", "type": event_type,
                                                         "data": {"object": {"id": intent_id}}}))


def expire(api, db, order_id):
    from app.services.order_service import expire_due_orders

    db.execute(text("UPDATE orders SET pickup_expires_at = now() - interval '1 minute' WHERE id = :id"), {"id": order_id})
    db.commit()
    in_session(api, expire_due_orders)


def cart_of(api, user):
    return call(api, user, "GET", "/cart/current")


def own_items(cart):
    return [(item["variant_id"], item["quantity"]) for item in cart["items"]]


def order_row(db, order_id):
    return tuple(db.execute(text("SELECT status, payment_status, fulfillment_status FROM orders WHERE id = :id"),
                            {"id": order_id}).one())


def test_stripe_failure_keeps_the_cart(hold_api, api_db, market, monkeypatch):
    import stripe

    def boom(**kwargs):
        raise RuntimeError("Stripe caído")

    add(hold_api, market)
    monkeypatch.setattr(stripe.PaymentIntent, "create", boom)
    result = hold_api.post("/api/payments/stripe/checkout", headers=headers(market.customer),
                           json={"pickup_branch_id": str(market.branches[0].id)})
    assert result.status_code == 400
    assert result.json()["message"].startswith("No se pudo iniciar el pago con Stripe")
    cart = cart_of(hold_api, market.customer)
    assert cart["status"] == "active" and own_items(cart) == [(str(market.own.variant.id), 1)]
    assert cart["pending_order_id"] is None
    assert api_db.execute(text("SELECT status, payment_status FROM orders")).one() == ("failed", "failed")
    assert stock(api_db, market.own.variant, market.branches[0]) == (9, 2)


def test_checkout_locks_cart_and_reports_pending_order(hold_api, api_db, market):
    add(hold_api, market)
    order = checkout(hold_api, market)
    cart = cart_of(hold_api, market.customer)
    assert cart["status"] == "checkout_pending" and own_items(cart) == [(str(market.own.variant.id), 1)]
    assert cart["pending_order_id"] == order["id"]
    expires = datetime.fromisoformat(cart["pending_order_expires_at"])
    assert abs(expires - (datetime.now(timezone.utc) + timedelta(minutes=40))) < timedelta(minutes=1)
    assert stock(api_db, market.own.variant, market.branches[0]) == (9, 3)


def test_repeated_checkout_reuses_the_pending_order(hold_api, api_db, market):
    add(hold_api, market)
    order = checkout(hold_api, market)
    again = checkout(hold_api, market)
    assert again["id"] == order["id"] and again["payment_intent_id"] == order["payment_intent_id"]
    assert api_db.execute(text("SELECT count(*) FROM orders")).scalar_one() == 1
    assert stock(api_db, market.own.variant, market.branches[0]) == (9, 3)
    rejected(hold_api, api_db, market.customer, "POST", "/payments/stripe/checkout", message=OTHER_BRANCH,
             json={"pickup_branch_id": str(market.branches[1].id)})


def test_paid_order_empties_the_cart(hold_api, api_db, market):
    from app.models.promotion_code import PromotionCode

    api_db.add(PromotionCode(tenant_id=market.own.tenant.id, code="HOLD5", discount_type="fixed", discount_value=5,
                             created_by=market.staff[0, "administrador"].id))
    api_db.commit()
    add(hold_api, market)
    call(hold_api, market.customer, "POST", "/cart/coupon", json={"code": "HOLD5"})
    order = checkout(hold_api, market)
    assert cart_of(hold_api, market.customer)["promotion_code"] == "HOLD5"  # kept while pending
    pay(hold_api, market, order)
    cart = cart_of(hold_api, market.customer)
    assert cart["status"] == "active" and cart["items"] == [] and cart["promotion_code_id"] is None
    assert cart["pending_order_id"] is None
    assert order_row(api_db, order["id"])[:2] == ("paid", "paid")
    assert stock(api_db, market.own.variant, market.branches[0]) == (8, 2)


def test_failed_card_payment_keeps_the_cart(hold_api, api_db, market):
    add(hold_api, market)
    order = checkout(hold_api, market)
    stripe_event(hold_api, order["payment_intent_id"], "payment_intent.payment_failed")
    assert order_row(api_db, order["id"]) == ("failed", "failed", "cancelled")
    assert stock(api_db, market.own.variant, market.branches[0]) == (9, 2)
    cart = cart_of(hold_api, market.customer)
    assert cart["status"] == "active" and own_items(cart) == [(str(market.own.variant.id), 1)]
    # The customer can retry with the same cart.
    assert checkout(hold_api, market)["id"] != order["id"]


def test_expired_order_empties_the_cart(hold_api, api_db, market):
    add(hold_api, market)
    order = checkout(hold_api, market)
    assert own_items(cart_of(hold_api, market.customer)) == [(str(market.own.variant.id), 1)]
    expire(hold_api, api_db, order["id"])
    assert order_row(api_db, order["id"]) == ("failed", "failed", "expired")
    assert stock(api_db, market.own.variant, market.branches[0]) == (9, 2)
    cart = cart_of(hold_api, market.customer)
    assert cart["status"] == "active" and cart["items"] == [] and cart["pending_order_id"] is None


def test_cancelled_order_keeps_the_cart(hold_api, api_db, market):
    add(hold_api, market)
    order = checkout(hold_api, market)
    call(hold_api, market.customer, "POST", f"/orders/{order['id']}/cancel")
    assert stock(api_db, market.own.variant, market.branches[0]) == (9, 2)
    cart = cart_of(hold_api, market.customer)
    assert cart["status"] == "active" and own_items(cart) == [(str(market.own.variant.id), 1)]
    add(hold_api, market)  # editable again
    assert own_items(cart_of(hold_api, market.customer)) == [(str(market.own.variant.id), 2)]


def test_locked_cart_rejects_changes(hold_api, api_db, market):
    cart = add(hold_api, market)
    checkout(hold_api, market)
    item = cart["items"][0]["id"]
    rejected(hold_api, api_db, market.customer, "POST", "/cart/items", message=LOCKED, json={
        "variant_id": str(market.own.variant.id), "branch_id": str(market.branches[0].id), "quantity": 1})
    rejected(hold_api, api_db, market.customer, "PATCH", f"/cart/items/{item}", message=LOCKED, json={"quantity": 2})
    rejected(hold_api, api_db, market.customer, "DELETE", f"/cart/items/{item}", message=LOCKED)
    rejected(hold_api, api_db, market.customer, "DELETE", "/cart/current", message=LOCKED)


def fund_wallet(db, user, amount):
    from app.models.wallet import UserWallet

    db.add(UserWallet(user_id=user.id, balance=Decimal(amount), currency="BOB"))
    db.commit()


def test_wallet_checkout_pays_and_empties_the_cart(hold_api, api_db, market):
    fund_wallet(api_db, market.customer, "100")
    add(hold_api, market)
    order = call(hold_api, market.customer, "POST", "/wallet/checkout", 201,
                 json={"pickup_branch_id": str(market.branches[0].id)})
    assert order["payment_status"] == "paid" and order["payment_method"] == "wallet"
    cart = cart_of(hold_api, market.customer)
    assert cart["status"] == "active" and cart["items"] == []
    assert stock(api_db, market.own.variant, market.branches[0]) == (8, 2)


def test_wallet_checkout_rejected_while_card_order_pending(hold_api, api_db, market):
    fund_wallet(api_db, market.customer, "100")
    add(hold_api, market)
    checkout(hold_api, market)
    rejected(hold_api, api_db, market.customer, "POST", "/wallet/checkout", message=LOCKED,
             json={"pickup_branch_id": str(market.branches[0].id)})


def test_order_displaced_by_offline_queue_keeps_the_cart(offline_api, api_db, market, till):
    first, _ = till
    add(offline_api, market)
    order = checkout(offline_api, market, offline_requested_at=ago(3))
    assert sync(offline_api, first, sale_op(market, minutes_ago=10))["synced_count"] == 1
    assert order_row(api_db, order["id"])[:2] == ("cancelled", "failed")
    cart = cart_of(offline_api, market.customer)
    assert cart["status"] == "active" and own_items(cart) == [(str(market.own.variant.id), 1)]


def test_offline_add_rejected_while_locked(offline_api, api_db, market):
    add(offline_api, market)
    checkout(offline_api, market)
    rejected(offline_api, api_db, market.customer, "POST", "/cart/items", message=LOCKED, json={
        "variant_id": str(market.own.variant.id), "branch_id": str(market.branches[0].id), "quantity": 1,
        "offline_requested_at": ago(5)})


def test_release_never_touches_another_users_cart(hold_api, api_db, market):
    add(hold_api, market)
    mine = checkout(hold_api, market)
    call(hold_api, market.other, "POST", "/cart/items", 201, json={
        "variant_id": str(market.own.variant.id), "branch_id": str(market.branches[0].id), "quantity": 1})
    theirs = call(hold_api, market.other, "POST", "/payments/stripe/checkout", 201,
                  json={"pickup_branch_id": str(market.branches[0].id)})
    assert own_items(cart_of(hold_api, market.customer)) == [(str(market.own.variant.id), 1)]
    expire(hold_api, api_db, mine["id"])
    other_cart = cart_of(hold_api, market.other)
    assert other_cart["status"] == "checkout_pending" and other_cart["pending_order_id"] == theirs["order_id"]
    assert own_items(other_cart) == [(str(market.own.variant.id), 1)]
    assert cart_of(hold_api, market.customer)["items"] == []
    assert stock(api_db, market.own.variant, market.branches[0]) == (9, 3)  # only the other's hold remains


def test_old_order_release_does_not_unlock_a_newer_orders_cart(hold_api, api_db, market):
    add(hold_api, market)
    old = checkout(hold_api, market)
    call(hold_api, market.customer, "POST", f"/orders/{old['id']}/cancel")
    new = checkout(hold_api, market)
    # A leftover older pending order (e.g. created before this change) expires later.
    api_db.execute(text("UPDATE orders SET status = 'pending', payment_status = 'pending', "
                        "fulfillment_status = 'pending_pickup', created_at = created_at - interval '1 hour' WHERE id = :id"),
                   {"id": old["id"]})
    api_db.execute(text("UPDATE inventory SET reserved_quantity = reserved_quantity + 1 WHERE variant_id = :v "
                        "AND branch_id = :b"), {"v": market.own.variant.id, "b": market.branches[0].id})
    api_db.commit()
    expire(hold_api, api_db, old["id"])
    cart = cart_of(hold_api, market.customer)
    assert cart["status"] == "checkout_pending" and cart["pending_order_id"] == new["id"]
    assert own_items(cart) == [(str(market.own.variant.id), 1)]
    assert stock(api_db, market.own.variant, market.branches[0]) == (9, 3)


def test_cart_read_expires_an_overdue_order(hold_api, api_db, market):
    add(hold_api, market)
    order = checkout(hold_api, market)
    api_db.execute(text("UPDATE orders SET pickup_expires_at = now() - interval '1 minute' WHERE id = :id"),
                   {"id": order["id"]})
    api_db.commit()
    cart = cart_of(hold_api, market.customer)  # no expiry loop: reading the cart expires it
    assert cart["status"] == "active" and cart["items"] == [] and cart["pending_order_id"] is None
    assert order_row(api_db, order["id"]) == ("failed", "failed", "expired")
    assert stock(api_db, market.own.variant, market.branches[0]) == (9, 2)


def test_repeated_delivery_checkout_needs_the_same_address_and_modality(delivery_api, api_db, market):
    address = {"address": "Av. San Martín 450", "reference": "Edificio azul", **NEAR}
    add(delivery_api, market)
    order = checkout(delivery_api, market, delivery=address)
    assert checkout(delivery_api, market, delivery=address)["id"] == order["id"]
    branch = str(market.branches[0].id)
    rejected(delivery_api, api_db, market.customer, "POST", "/payments/stripe/checkout", message=OTHER_ADDRESS,
             json={"pickup_branch_id": branch, "delivery": {**address, "address": "Calle Junín 120"}})
    rejected(delivery_api, api_db, market.customer, "POST", "/payments/stripe/checkout", message=OTHER_ADDRESS,
             json={"pickup_branch_id": branch, "delivery": {**address, "latitude": NEAR["latitude"] + 0.001}})
    rejected(delivery_api, api_db, market.customer, "POST", "/payments/stripe/checkout", message=OTHER_MODE,
             json={"pickup_branch_id": branch})
    assert stock(api_db, market.own.variant, market.branches[0]) == (9, 3)


def test_paying_an_older_order_keeps_the_cart_locked_by_a_newer_one(hold_api, api_db, market):
    """An older pending order (e.g. created before carts were kept) is paid while a newer one holds the lock."""
    from app.schemas.order_schema import PaymentMethodEnum
    from app.services.order_service import _locked_cart, _new_order

    add(hold_api, market)
    older = checkout(hold_api, market)

    def newer_order(db):
        cart = _locked_cart(db, market.customer.id)
        order = _new_order(db, cart, market.customer.id, market.branches[0].id, PaymentMethodEnum.stripe)
        db.commit()
        return str(order.id)

    newer = in_session(hold_api, newer_order)
    pay(hold_api, market, older)
    cart = cart_of(hold_api, market.customer)
    assert cart["status"] == "checkout_pending" and cart["pending_order_id"] == newer
    assert own_items(cart) == [(str(market.own.variant.id), 1)]
    assert stock(api_db, market.own.variant, market.branches[0]) == (8, 3)  # older sold, newer still held


def second_variant(db, market):
    """Another variant of the own product with stock in branch 0 (10 units, 2 already held)."""
    from app.models.inventory import Inventory
    from app.models.product_variant import ProductVariant
    from app.schemas.catalog_enums import ProductStatusEnum

    base = market.own.variant
    other = ProductVariant(tenant_id=base.tenant_id, product_id=base.product_id, sku="SKU-0-L", price=base.price,
                           size_id=db.execute(text("SELECT id FROM sizes WHERE name = 'L'")).scalar(),
                           color_id=base.color_id, status=ProductStatusEnum.active)
    db.add(other)
    db.flush()
    db.add(Inventory(tenant_id=other.tenant_id, variant_id=other.id, branch_id=market.branches[0].id,
                     quantity=10, reserved_quantity=2, minimum_stock=0))
    db.commit()
    return other


@pytest.mark.parametrize("line_order", ["sorted", "reverse"])
def test_lock_ordering_does_not_change_release_or_consume(hold_api, api_db, market, line_order):
    """Stock is locked in variant-id order; the order of the lines must not change any result."""
    own, other = market.own.variant, second_variant(api_db, market)
    variants = sorted([own, other], key=lambda v: str(v.id), reverse=line_order == "reverse")
    branch = market.branches[0]

    def stocks():
        return {"own": stock(api_db, own, branch), "other": stock(api_db, other, branch)}

    for variant in variants:
        call(hold_api, market.customer, "POST", "/cart/items", 201, json={
            "variant_id": str(variant.id), "branch_id": str(branch.id), "quantity": 1})
    first = checkout(hold_api, market)
    # Lines are added in sorted or reverse variant order; the order's own item order is not controllable.
    assert {item["variant_id"] for item in first["items"]} == {str(v.id) for v in variants}
    assert stocks() == {"own": (9, 3), "other": (10, 3)}
    call(hold_api, market.customer, "POST", f"/orders/{first['id']}/cancel")  # release
    assert stocks() == {"own": (9, 2), "other": (10, 2)}
    second = checkout(hold_api, market)  # the cart kept both lines
    pay(hold_api, market, second)  # consume
    assert stocks() == {"own": (8, 2), "other": (9, 2)}
    assert cart_of(hold_api, market.customer)["items"] == []


def test_reservation_transfer_after_an_overdue_order(hold_api, api_db, market):
    add(hold_api, market)
    order = checkout(hold_api, market)
    reservation = purchase_pending(hold_api, market)
    api_db.execute(text("UPDATE orders SET pickup_expires_at = now() - interval '1 minute' WHERE id = :id"),
                   {"id": order["id"]})
    api_db.commit()
    cart = call(hold_api, market.customer, "POST", f"/reservations/{reservation['id']}/to-cart")
    assert cart["status"] == "active" and own_items(cart) == [(str(market.own.variant.id), 1)]
    assert order_row(api_db, order["id"]) == ("failed", "failed", "expired")
    again = call(hold_api, market.customer, "POST", f"/reservations/{reservation['id']}/to-cart")
    assert own_items(again) == [(str(market.own.variant.id), 1)]
