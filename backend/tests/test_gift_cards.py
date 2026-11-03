"""CU18: Gift cards issuance, purchase, verification and QR code."""
import pytest

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_marketplace_transactions import call, market, market_api, rejected  # noqa: F401


@pytest.fixture
def gift_card_api(market_api):
    from app.routes import gift_card_routes

    market_api.app.include_router(gift_card_routes.router, prefix="/api")
    return market_api


def test_code_format_and_qr_generation():
    from app.services.gift_card_service import make_qr_data_uri
    qr = make_qr_data_uri("GIFT-2026-X89Q")
    assert qr.startswith("data:image/png;base64,")


def test_purchase_gift_card_success(gift_card_api, api_db, market):
    payload = {
        "amount": 50.00,
        "recipient_name": "Camila Morales",
        "recipient_email": "camila@gmail.com",
        "custom_message": "¡Feliz cumpleaños Cami!",
        "payment_method": "stripe",
    }
    data = call(
        gift_card_api,
        market.customer,
        "POST",
        "/gift-cards/purchase",
        201,
        expected_message="Tarjeta de regalo adquirida y enviada por correo al destinatario",
        json=payload,
    )
    assert data["card_code"].startswith("GIFT-")
    assert data["amount"] == 50.00
    assert data["recipient_email"] == "camila@gmail.com"
    assert data["qr_code_url"].startswith("data:image/png;base64,")


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
    data = call(gift_card_api, market.customer, "POST", "/gift-cards/purchase", 201, json=payload)
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
    call(gift_card_api, market.customer, "POST", "/gift-cards/purchase", 201, json={
        "amount": 25.00, "recipient_name": "Dest 1", "recipient_email": "d1@mail.com"
    })
    call(gift_card_api, market.customer, "POST", "/gift-cards/purchase", 201, json={
        "amount": 75.00, "recipient_name": "Dest 2", "recipient_email": "d2@mail.com"
    })
    purchases = call(gift_card_api, market.customer, "GET", "/gift-cards/my-purchases", 200)
    assert len(purchases) >= 2
    assert purchases[0]["amount"] in ("75.00", 75.00, "25.00", 25.00)
