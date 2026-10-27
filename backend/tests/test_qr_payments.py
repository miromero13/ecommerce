"""Simulated QR payments: web checkout and in-store cashier, collected by the platform."""
from decimal import Decimal

import pytest
from sqlalchemy import text

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_marketplace_transactions import add, call, market, market_api, rejected, stock  # noqa: F401


def ledger(db):
    return [tuple(r) for r in db.execute(text("SELECT source_type, method, gross_amount FROM payment_transactions"))]


def test_web_order_paid_by_qr_is_consumed_and_recorded(market_api, api_db, market):
    add(market_api, market)
    data = call(market_api, market.customer, "POST", "/payments/qr/checkout", 201,
                json={"pickup_branch_id": str(market.branches[0].id)})
    order, qr = data["order"], data["qr"]
    assert order["payment_method"] == "qr" and order["payment_status"] == "pending"
    assert qr["qr_image"].startswith("data:image/png;base64,") and Decimal(str(qr["amount"])) == Decimal("25")

    rejected(market_api, api_db, market.other, "POST", f"/payments/qr/{qr['reference']}/simulate-payment", 404,
             "Pago QR no encontrado")
    quantity, reserved = stock(api_db, market.own.variant, market.branches[0])
    paid = call(market_api, market.customer, "POST", f"/payments/qr/{qr['reference']}/simulate-payment",
                expected_message="Pago QR confirmado")
    assert paid["status"] == "used"
    mine = call(market_api, market.customer, "GET", f"/orders/{order['id']}")
    assert mine["payment_status"] == "paid"
    assert stock(api_db, market.own.variant, market.branches[0]) == (quantity - 1, reserved - 1)
    assert ledger(api_db) == [("order", "qr", Decimal("25.00"))]


def test_cashier_qr_sale_requires_payment_and_cannot_reuse_it(market_api, api_db, market):
    cashier = market.staff[0, "cajero"]
    body = {"items": [{"variant_id": str(market.own.variant.id), "quantity": 1}]}
    qr = call(market_api, cashier, "POST", "/payments/qr/sale-intent", 201, json=body)
    assert Decimal(str(qr["amount"])) == Decimal("25")
    sale_body = {**body, "payment_method": "qr", "qr_reference": qr["reference"]}

    rejected(market_api, api_db, cashier, "POST", "/sales/", 400, "El cliente aún no pagó el código QR", json=sale_body)
    call(market_api, cashier, "POST", f"/payments/qr/{qr['reference']}/simulate-payment")
    sale = call(market_api, cashier, "POST", "/sales/", 201, json=sale_body)
    assert sale["payment_method"] == "qr"
    assert ledger(api_db) == [("sale", "qr", Decimal("25.00"))]
    rejected(market_api, api_db, cashier, "POST", "/sales/", 400, "El código QR ya fue utilizado en otra venta", json=sale_body)


def test_bank_webhook_requires_the_shared_secret(market_api, api_db, market, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "qr_webhook_secret", "bank-secret")
    qr = call(market_api, market.staff[0, "cajero"], "POST", "/payments/qr/sale-intent", 201,
              json={"items": [{"variant_id": str(market.own.variant.id), "quantity": 1}]})
    bad = market_api.post("/api/payments/qr/webhook", json={"reference": qr["reference"]},
                          headers={"X-QR-Webhook-Secret": "wrong"})
    assert bad.status_code == 401
    ok = market_api.post("/api/payments/qr/webhook", json={"reference": qr["reference"]},
                         headers={"X-QR-Webhook-Secret": "bank-secret"})
    assert ok.json()["data"]["status"] == "paid"
