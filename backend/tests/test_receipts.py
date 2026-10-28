"""Every payment transaction issues a simple receipt (comprobante): PDF download and email to the payer."""
import asyncio
import base64
from decimal import Decimal

import pytest

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_employee_authorization import headers
from test_marketplace_transactions import add, call, checkout, market, market_api, pay, rejected, reserve  # noqa: F401


@pytest.fixture
def rcpt_api(market_api):
    from app.routes import receipt_routes, subscription_routes

    market_api.app.include_router(receipt_routes.router, prefix="/api")
    market_api.app.include_router(subscription_routes.router, prefix="/api")
    return market_api


def receipts(api, user, **params):
    return [(r["number"], r["kind"], r["payment_method"], Decimal(str(r["total"])))
            for r in call(api, user, "GET", "/receipts", params=params)]


def paid_order(api, market, group=None, branch=None):
    add(api, market, group, branch)
    order = checkout(api, market, branch)
    pay(api, market, order)
    return order


def test_paid_web_order_issues_one_receipt_numbered_per_company(rcpt_api, api_db, market):
    order = paid_order(rcpt_api, market)
    pay(rcpt_api, market, order)  # Stripe retries the webhook: still one receipt
    assert receipts(rcpt_api, market.customer) == [("C-000001", "order", "card", Decimal("25.00"))]
    paid_order(rcpt_api, market)
    paid_order(rcpt_api, market, market.foreign, market.branches[2])  # another company: its own sequence
    numbers = {(r["number"], r["tenant_id"]) for r in call(rcpt_api, market.customer, "GET", "/receipts")}
    assert numbers == {("C-000001", str(market.own.tenant.id)), ("C-000002", str(market.own.tenant.id)),
                       ("C-000001", str(market.foreign.tenant.id))}

    pdf = rcpt_api.get(f"/api/receipts/order/{order['id']}/pdf", headers=headers(market.customer))
    assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf" and pdf.content[:4] == b"%PDF"
    rejected(rcpt_api, api_db, market.other, "GET", f"/receipts/order/{order['id']}/pdf", 404, "Comprobante no encontrado")
    # Staff of the company see it; staff of another company never do.
    assert receipts(rcpt_api, market.staff[0, "administrador"], kind="order")[0][1] == "order"
    assert receipts(rcpt_api, market.staff[2, "administrador"], kind="order") == [("C-000001", "order", "card", Decimal("25.00"))]


def test_till_sale_receipt_shows_cash_received_and_change(rcpt_api, api_db, market):
    cashier = market.staff[0, "cajero"]
    sale = call(rcpt_api, cashier, "POST", "/sales/", 201, json={
        "items": [{"variant_id": str(market.own.variant.id), "quantity": 1}], "cash_received": "30"})
    assert sale["receipt_id"]
    [receipt] = call(rcpt_api, cashier, "GET", "/receipts", params={"kind": "sale"})
    assert (receipt["payment_method"], receipt["customer_name"]) == ("cash", "Cliente en tienda")
    assert {row["label"]: row["amount"] for row in receipt["summary"]}["Cambio entregado"] == "5.00"
    # A cashier of another branch never sees it.
    rejected(rcpt_api, api_db, market.staff[1, "cajero"], "GET", f"/receipts/sale/{sale['id']}/pdf", 404,
             "Comprobante no encontrado")


def test_deposit_and_subscription_payments_issue_receipts(rcpt_api, api_db, market):
    reserve(rcpt_api, market)
    assert receipts(rcpt_api, market.customer) == [("C-000001", "reservation_deposit", "card", Decimal("12.50"))]

    admin = market.staff[0, "administrador"]
    call(rcpt_api, admin, "POST", "/saas/subscriptions/change-plan", json={"plan_id": "plan_basic", "billing_cycle": "monthly"})
    # The platform's own sequence; the paying company's admin sees it, another company's admin does not.
    assert ("P-000001", "subscription", "card", Decimal("49.00")) in receipts(rcpt_api, admin, kind="subscription")
    assert receipts(rcpt_api, market.staff[2, "administrador"], kind="subscription") == []


def test_receipts_are_emailed_with_the_pdf_and_can_be_resent(rcpt_api, api_db, market):
    from sqlalchemy.orm import Session

    from app.services.receipt_service import send_pending_receipts

    class FakeMailer:
        def __init__(self):
            self.sent = []

        async def send_email(self, **message):
            self.sent.append(message)
            return True

    order = paid_order(rcpt_api, market)
    mailer = FakeMailer()
    factory = lambda: Session(bind=api_db.bind, join_transaction_mode="create_savepoint")  # noqa: E731
    assert asyncio.run(send_pending_receipts(factory, mailer)) == 1
    message = mailer.sent[0]
    assert message["to"] == market.customer.email and message["subject"].startswith("Comprobante de pago C-000001")
    attachment = message["attachments"][0]
    assert attachment["filename"] == "comprobante-C-000001.pdf" and base64.b64decode(attachment["content"])[:4] == b"%PDF"
    assert asyncio.run(send_pending_receipts(factory, mailer)) == 0  # already delivered

    resent = call(rcpt_api, market.customer, "POST", f"/receipts/order/{order['id']}/resend",
                  expected_message=f"Enviaremos el comprobante a {market.customer.email}")
    assert resent["emailed_at"] is None
    assert asyncio.run(send_pending_receipts(factory, mailer)) == 1
