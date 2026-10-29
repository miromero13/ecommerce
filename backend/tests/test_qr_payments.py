"""Simulated QR payments: only at the store's till, collected by the platform (online is Stripe only)."""
from decimal import Decimal

import pytest
from sqlalchemy import text

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_employee_authorization import headers
from test_marketplace_transactions import add, call, market, market_api, rejected  # noqa: F401


def ledger(db):
    return [tuple(r) for r in db.execute(text("SELECT source_type, method, gross_amount FROM payment_transactions"))]


def test_qr_is_not_offered_for_online_orders_or_deposits(market_api, api_db, market):
    add(market_api, market)
    auth = headers(market.customer)
    web = market_api.post("/api/payments/qr/checkout", headers=auth, json={"pickup_branch_id": str(market.branches[0].id)})
    deposit = market_api.post(f"/api/payments/qr/reservations/{market.branches[0].id}", headers=auth)
    # Online payments are Stripe only: neither endpoint exists (405 when the path matches GET /qr/{reference}).
    assert web.status_code in (404, 405) and deposit.status_code == 404


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
