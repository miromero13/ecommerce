"""CU18: Gift cards issuance, Stripe payment, verification and QR code."""
from types import SimpleNamespace

import pytest

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_marketplace_transactions import call, market, market_api, rejected, stripe_webhook  # noqa: F401


@pytest.fixture
def gift_stripe(monkeypatch):
    """Fake Stripe: every PaymentIntent is created and, when retrieved, reported as charged (status)."""
    import stripe
    from app.core.config import settings

    intents = {}

    def create(**kwargs):
        intent = {"id": f"pi_gift_{len(intents) + 1}", "client_secret": "secret_test", "status": "succeeded",
                  "amount": kwargs["amount"], "currency": kwargs["currency"], "metadata": kwargs["metadata"]}
        intents[intent["id"]] = intent
        return SimpleNamespace(id=intent["id"], client_secret=intent["client_secret"])

    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_fake")
    monkeypatch.setattr(stripe.PaymentIntent, "create", create)
    monkeypatch.setattr(stripe.PaymentIntent, "retrieve", lambda intent_id, **kwargs: intents[intent_id])
    return intents


@pytest.fixture
def gift_card_api(market_api, gift_stripe):
    from app.routes import gift_card_routes

    market_api.app.include_router(gift_card_routes.router, prefix="/api")
    return market_api


def buy_gift_card(api, user, json, **kwargs):
    """Purchase (PaymentIntent) + card paid in Stripe + confirm-payment, as the web/mobile client does."""
    intent = call(api, user, "POST", "/gift-cards/purchase", 201, json=json)
    return call(api, user, "POST", f"/gift-cards/{intent['id']}/confirm-payment", 200, **kwargs)


def test_code_format_and_qr_generation():
    from app.services.gift_card_service import make_qr_data_uri
    qr = make_qr_data_uri("GIFT-2026-X89Q")
    assert qr.startswith("data:image/png;base64,")


def test_purchase_gift_card_success(gift_card_api, api_db, market, gift_stripe):
    payload = {
        "amount": 50.00,
        "recipient_name": "Camila Morales",
        "recipient_email": "camila@gmail.com",
        "custom_message": "¡Feliz cumpleaños Cami!",
        "payment_method": "stripe",
    }
    intent = call(gift_card_api, market.customer, "POST", "/gift-cards/purchase", 201,
                  expected_message="Pago con Stripe iniciado: ingresa los datos de la tarjeta", json=payload)
    assert intent["client_secret"] == "secret_test"
    assert intent["status"] == "pending_payment"
    stripe_intent = next(iter(gift_stripe.values()))
    assert stripe_intent["amount"] == 5000
    assert stripe_intent["metadata"] == {"gift_card_id": intent["id"]}

    data = call(gift_card_api, market.customer, "POST", f"/gift-cards/{intent['id']}/confirm-payment", 200,
                expected_message="Tarjeta de regalo adquirida y enviada por correo al destinatario")
    assert data["card_code"].startswith("GIFT-")
    assert data["amount"] == 50.00
    assert data["recipient_email"] == "camila@gmail.com"
    assert data["qr_code_url"].startswith("data:image/png;base64,")


def test_unpaid_gift_card_is_not_issued(gift_card_api, api_db, market, gift_stripe):
    intent = call(gift_card_api, market.customer, "POST", "/gift-cards/purchase", 201, json={
        "amount": 30.00, "recipient_name": "Sin Pago", "recipient_email": "sp@mail.com"})
    next(iter(gift_stripe.values()))["status"] = "requires_payment_method"
    rejected(gift_card_api, api_db, market.customer, "POST", f"/gift-cards/{intent['id']}/confirm-payment", 400,
             "El pago con tarjeta todavía no se confirmó. La tarjeta se emitirá al confirmarse el cobro.")
    assert call(gift_card_api, market.customer, "GET", "/gift-cards/my-purchases", 200) == []


def test_stripe_webhook_activates_gift_card(gift_card_api, api_db, market):
    intent = call(gift_card_api, market.customer, "POST", "/gift-cards/purchase", 201, json={
        "amount": 40.00, "recipient_name": "Webhook", "recipient_email": "wh@mail.com"})
    stripe_webhook(gift_card_api, "pi_gift_1", 4000, "bob", {"gift_card_id": intent["id"]})
    purchases = call(gift_card_api, market.customer, "GET", "/gift-cards/my-purchases", 200)
    assert [card["status"] for card in purchases] == ["active"]


def test_purchase_gift_card_min_amount(gift_card_api, api_db, market):
    payload = {
        "amount": 5.00,
        "recipient_name": "Camila Morales",
        "recipient_email": "camila@gmail.com",
        "custom_message": "¡Hola!",
    }
    rejected(
        gift_card_api,
        api_db,
        market.customer,
        "POST",
        "/gift-cards/purchase",
        400,
        "El importe de la tarjeta de regalo debe ser mayor o igual a $10.00",
        json=payload,
    )


def test_verify_gift_card_success_and_not_found(gift_card_api, api_db, market):
    payload = {
        "amount": 100.00,
        "recipient_name": "Andrea Silva",
        "recipient_email": "andrea@gmail.com",
    }
    data = buy_gift_card(gift_card_api, market.customer, payload)
    code = data["card_code"]

    verified = call(gift_card_api, market.customer, "GET", f"/gift-cards/verify/{code}", 200,
                    expected_message="Tarjeta de regalo verificada exitosamente")
    assert verified["code"] == code
    assert float(verified["amount"]) == 100.00
    assert verified["status"] == "active"

    rejected(
        gift_card_api,
        api_db,
        market.customer,
        "GET",
        "/gift-cards/verify/GIFT-FAKE-9999",
        404,
        "Tarjeta de regalo no encontrada con el código ingresado",
    )


def test_list_my_purchases(gift_card_api, api_db, market):
    buy_gift_card(gift_card_api, market.customer, {
        "amount": 25.00, "recipient_name": "Dest 1", "recipient_email": "d1@mail.com"
    })
    buy_gift_card(gift_card_api, market.customer, {
        "amount": 75.00, "recipient_name": "Dest 2", "recipient_email": "d2@mail.com"
    })
    purchases = call(gift_card_api, market.customer, "GET", "/gift-cards/my-purchases", 200)
    assert len(purchases) >= 2
    assert purchases[0]["amount"] in ("75.00", 75.00, "25.00", 25.00)
