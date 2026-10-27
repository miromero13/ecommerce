"""D1: 50 % non-refundable reservation deposit, paid online (QR or card)."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import text

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_marketplace_transactions import call, market, market_api, rejected, stock  # noqa: F401


def create(api, market):
    return call(api, market.customer, "POST", "/reservations/", 201, json={
        "branch_id": str(market.branches[0].id), "visit_date": (date.today() + timedelta(days=2)).isoformat(),
        "items": [{"variant_id": str(market.own.variant.id), "quantity": 1}],
    })


def deposits(db):
    return [tuple(r) for r in db.execute(text(
        "SELECT source_type, method, gross_amount FROM payment_transactions WHERE source_type = 'reservation_deposit'"))]


def test_reservation_waits_for_its_deposit_while_holding_stock(market_api, api_db, market):
    before = stock(api_db, market.own.variant, market.branches[0])
    reservation = create(market_api, market)
    assert (reservation["status"], reservation["deposit_status"]) == ("pending_payment", "pending")
    assert Decimal(str(reservation["deposit_amount"])) == Decimal("12.50")
    assert stock(api_db, market.own.variant, market.branches[0]) == (before[0], before[1] + 1)

    qr = call(market_api, market.customer, "POST", f"/payments/qr/reservations/{reservation['id']}", 201)
    assert Decimal(str(qr["amount"])) == Decimal("12.50")
    call(market_api, market.customer, "POST", f"/payments/qr/{qr['reference']}/simulate-payment")
    paid = call(market_api, market.customer, "GET", f"/reservations/{reservation['id']}")
    assert (paid["status"], paid["deposit_status"]) == ("pending", "paid")
    assert deposits(api_db) == [("reservation_deposit", "qr", Decimal("12.50"))]
    rejected(market_api, api_db, market.customer, "POST", f"/payments/qr/reservations/{reservation['id']}", 400,
             "La reserva ya no espera el pago del anticipo")


def test_unpaid_deposit_expires_and_releases_stock(market_api, api_db, market):
    before = stock(api_db, market.own.variant, market.branches[0])
    reservation = create(market_api, market)
    api_db.execute(text("UPDATE reservations SET payment_expires_at = :at"),
                   {"at": datetime.now(timezone.utc) - timedelta(minutes=1)})
    api_db.commit()
    expired = call(market_api, market.customer, "GET", f"/reservations/{reservation['id']}")
    assert (expired["status"], expired["deposit_status"]) == ("expired", "none")
    assert stock(api_db, market.own.variant, market.branches[0]) == before


def test_cancelled_reservation_forfeits_the_deposit(market_api, api_db, market):
    reservation = create(market_api, market)
    qr = call(market_api, market.customer, "POST", f"/payments/qr/reservations/{reservation['id']}", 201)
    call(market_api, market.customer, "POST", f"/payments/qr/{qr['reference']}/simulate-payment")
    cancelled = call(market_api, market.customer, "PATCH", f"/reservations/{reservation['id']}/cancel")
    assert (cancelled["status"], cancelled["deposit_status"]) == ("cancelled", "forfeited")
    assert deposits(api_db) == [("reservation_deposit", "qr", Decimal("12.50"))]  # never refunded


def test_card_deposit_is_confirmed_by_the_stripe_webhook(market_api, api_db, market):
    from app.models.reservation import Reservation
    from app.services.order_service import process_stripe_event

    reservation = create(market_api, market)
    row = api_db.query(Reservation).filter(Reservation.id == reservation["id"]).one()
    row.stripe_payment_intent_id = "pi_deposit"
    api_db.commit()
    process_stripe_event(api_db, {"id": "evt_dep", "type": "payment_intent.succeeded", "data": {"object": {
        "id": "pi_deposit", "amount": 1250, "metadata": {"reservation_id": reservation["id"]}}}})
    api_db.refresh(row)
    assert (row.status.value, row.deposit_status) == ("pending", "paid")
    assert deposits(api_db) == [("reservation_deposit", "card", Decimal("12.50"))]


def test_card_deposit_intent_charges_half_with_reservation_metadata(market_api, api_db, market, monkeypatch):
    import stripe
    from types import SimpleNamespace
    from app.core.config import settings

    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_fake")
    intents = []
    monkeypatch.setattr(stripe.PaymentIntent, "create", lambda **kwargs: intents.append(kwargs) or SimpleNamespace(
        id="pi_dep_1", client_secret="secret_dep"))
    reservation = create(market_api, market)

    data = call(market_api, market.customer, "POST", f"/payments/stripe/reservations/{reservation['id']}",
                expected_message="Pago del anticipo con tarjeta iniciado")
    assert data == {"client_secret": "secret_dep", "payment_intent_id": "pi_dep_1"}
    assert (intents[0]["amount"], intents[0]["currency"], intents[0]["metadata"]) == (
        1250, "bob", {"reservation_id": reservation["id"]})
    rejected(market_api, api_db, market.other, "POST", f"/payments/stripe/reservations/{reservation['id']}", 404,
             "Reserva no encontrada")
