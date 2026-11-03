"""CU19: Store wallet balance, gift card redemptions, transactions and wallet payments."""
from decimal import Decimal
import pytest

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_marketplace_transactions import add, call, market, market_api, rejected  # noqa: F401


@pytest.fixture
def wallet_api(market_api):
    from app.routes import gift_card_routes, wallet_routes

    market_api.app.include_router(gift_card_routes.router, prefix="/api")
    market_api.app.include_router(wallet_routes.router, prefix="/api")
    return market_api


def test_wallet_schemas_and_conversions():
    from app.schemas.wallet_schema import WalletBalanceResponse, WalletRedeemResponse, WalletConvertPointsResponse
    bal = WalletBalanceResponse(balance=Decimal("150.75"), currency="BOB")
    assert bal.balance == Decimal("150.75")
    assert bal.currency == "BOB"

    redeem = WalletRedeemResponse(credited_amount=Decimal("50.00"), new_balance=Decimal("200.75"))
    assert redeem.credited_amount == Decimal("50.00")
    assert redeem.new_balance == Decimal("200.75")

    conv = WalletConvertPointsResponse(converted_points=50, credited_amount=Decimal("5.00"), new_balance=Decimal("205.75"), tenant_name="Tienda")
    assert conv.converted_points == 50
    assert conv.credited_amount == Decimal("5.00")


def test_wallet_initial_balance_is_zero(wallet_api, api_db, market):
    data = call(wallet_api, market.customer, "GET", "/wallet/balance", 200,
                expected_message="Saldo de billetera virtual obtenido")
    assert data["balance"] == 0.0
    assert data["currency"] == "BOB"


def test_redeem_gift_card_credits_wallet_and_records_transaction(wallet_api, api_db, market):
    card = call(
        wallet_api,
        market.customer,
        "POST",
        "/gift-cards/purchase",
        201,
        json={
            "amount": 50.00,
            "recipient_name": "Yo Mismo",
            "recipient_email": market.customer.email,
        },
    )
    code = card["card_code"]

    redeem_res = call(
        wallet_api,
        market.customer,
        "POST",
        "/wallet/redeem-gift-card",
        200,
        expected_message="Gift Card canjeada exitosamente. Se acreditaron $50.00 en tu saldo.",
        json={"card_code": code},
    )
    assert redeem_res["credited_amount"] == 50.0
    assert redeem_res["new_balance"] == 50.0

    bal = call(wallet_api, market.customer, "GET", "/wallet/balance", 200)
    assert bal["balance"] == 50.0

    txs = call(wallet_api, market.customer, "GET", "/wallet/transactions", 200,
               expected_message="Movimientos de billetera obtenidos exitosamente")
    assert len(txs) == 1
    assert txs[0]["type"] == "credit"
    assert txs[0]["amount"] == 50.0
    assert txs[0]["concept"] == "gift_card_redeem"


def test_redeem_same_card_twice_is_rejected(wallet_api, api_db, market):
    card = call(
        wallet_api,
        market.customer,
        "POST",
        "/gift-cards/purchase",
        201,
        json={"amount": 30.00, "recipient_name": "Test", "recipient_email": "t@test.com"},
    )
    code = card["card_code"]
    call(wallet_api, market.customer, "POST", "/wallet/redeem-gift-card", 200, json={"card_code": code})

    rejected(
        wallet_api,
        api_db,
        market.customer,
        "POST",
        "/wallet/redeem-gift-card",
        400,
        "El código de la tarjeta de regalo no es válido o ya fue canjeado",
        json={"card_code": code},
    )


def test_redeem_invalid_code_rejected(wallet_api, api_db, market):
    rejected(
        wallet_api,
        api_db,
        market.customer,
        "POST",
        "/wallet/redeem-gift-card",
        404,
        "La tarjeta de regalo no existe o ha expirado",
        json={"card_code": "GIFT-INVALID-0000"},
    )


def test_wallet_checkout_success_and_insufficient_funds(wallet_api, api_db, market):
    # Set price to 100
    market.own.variant.price = 100
    api_db.commit()

    add(wallet_api, market)

    # Balance is 0 -> should reject
    rejected(
        wallet_api,
        api_db,
        market.customer,
        "POST",
        "/wallet/checkout",
        400,
        "Saldo insuficiente en la billetera virtual para completar la operación",
        json={"pickup_branch_id": str(market.branches[0].id)},
    )

    # Buy and redeem a $200 gift card
    card = call(
        wallet_api,
        market.customer,
        "POST",
        "/gift-cards/purchase",
        201,
        json={"amount": 200.00, "recipient_name": "Payer", "recipient_email": market.customer.email},
    )
    call(wallet_api, market.customer, "POST", "/wallet/redeem-gift-card", 200, json={"card_code": card["card_code"]})

    # Now checkout succeeds
    order = call(
        wallet_api,
        market.customer,
        "POST",
        "/wallet/checkout",
        201,
        expected_message="Pedido pagado exitosamente con tu Billetera Digital",
        json={"pickup_branch_id": str(market.branches[0].id)},
    )
    assert order["payment_method"] == "wallet"
    assert order["payment_status"] == "paid"

    bal = call(wallet_api, market.customer, "GET", "/wallet/balance", 200)
    assert bal["balance"] == 100.0

    txs = call(wallet_api, market.customer, "GET", "/wallet/transactions", 200)
    assert any(t["type"] == "debit" and t["concept"] == "order_payment" for t in txs)
