"""Platform collection ledger and daily settlements to each company's bank account."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import text

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_marketplace_transactions import add, call, market, market_api, rejected  # noqa: F401
from test_phase0_business_flows import _stripe_paid_order


@pytest.fixture
def payouts_api(market_api, api_db, market):
    from app.models.user import User
    from app.routes import payout_routes
    from app.schemas.enums import GenderEnum, RolEnum

    market_api.app.include_router(payout_routes.router, prefix="/api")
    market.superadmin = User(name="Root", email="root@example.com", hashed_password="unused",
                             gender=GenderEnum.femenino, rol=RolEnum.superadministrador, is_active=True)
    api_db.add(market.superadmin)
    market.own.tenant.platform_fee_percent = 10
    api_db.commit()
    return market_api


def ledger(db):
    return [tuple(row) for row in db.execute(text(
        "SELECT tenant_id, source_type, method, gross_amount, fee_amount, net_amount, settlement_id "
        "FROM payment_transactions ORDER BY created_at"))]


def backdate(db, days=1):
    db.execute(text("UPDATE payment_transactions SET created_at = :at"),
               {"at": datetime.now(timezone.utc) - timedelta(days=days)})
    db.commit()


def test_card_payment_is_recorded_for_its_company_with_fee(payouts_api, api_db, market):
    order = _stripe_paid_order(payouts_api, api_db, market)
    assert ledger(api_db) == [(market.own.tenant.id, "order", "card", Decimal(order["total_amount"]),
                               Decimal("2.50"), Decimal("22.50"), None)]


def test_till_cash_sale_never_enters_the_platform_ledger(payouts_api, api_db, market):
    # Cash only exists in the store's till: it stays with the company.
    call(payouts_api, market.staff[0, "cajero"], "POST", "/sales/", 201,
         json={"items": [{"variant_id": str(market.own.variant.id), "quantity": 1}]})
    assert ledger(api_db) == []


def test_daily_run_settles_yesterday_per_company_once(payouts_api, api_db, market):
    from app.services.payout_service import run_daily_settlements

    _stripe_paid_order(payouts_api, api_db, market)
    assert run_daily_settlements(api_db) == []  # today's payments wait for tomorrow's run
    backdate(api_db)

    settlements = run_daily_settlements(api_db)
    assert run_daily_settlements(api_db) == []
    assert [(s.tenant_id, s.period_date, s.gross_amount, s.fee_amount, s.net_amount, s.transactions_count)
            for s in settlements] == [(market.own.tenant.id, date.today() - timedelta(days=1),
                                       Decimal("25.00"), Decimal("2.50"), Decimal("22.50"), 1)]
    assert ledger(api_db)[0][-1] == settlements[0].id


def test_company_sees_only_its_settlements_and_superadmin_pays_them(payouts_api, api_db, market):
    from app.services.payout_service import run_daily_settlements

    admin, foreign_admin = market.staff[0, "administrador"], market.staff[2, "administrador"]
    call(payouts_api, admin, "PUT", "/payouts/bank-account", json={
        "bank_name": "Banco Unión", "bank_account_number": "100200300", "bank_account_holder": "Alpha SRL"})
    _stripe_paid_order(payouts_api, api_db, market)
    backdate(api_db)
    settlement_id = str(run_daily_settlements(api_db)[0].id)

    assert [s["id"] for s in call(payouts_api, admin, "GET", "/payouts/settlements")] == [settlement_id]
    assert call(payouts_api, foreign_admin, "GET", "/payouts/settlements") == []
    rejected(payouts_api, api_db, admin, "PATCH", f"/payouts/settlements/{settlement_id}/paid", 403,
             json={"transfer_reference": "TRX-1"})

    paid = call(payouts_api, market.superadmin, "PATCH", f"/payouts/settlements/{settlement_id}/paid",
                expected_message="Liquidación marcada como transferida", json={"transfer_reference": "TRX-1"})
    assert (paid["status"], paid["transfer_reference"], paid["bank_account_number"]) == ("paid", "TRX-1", "100200300")
    rejected(payouts_api, api_db, market.superadmin, "PATCH", f"/payouts/settlements/{settlement_id}/paid", 409,
             "La liquidación ya fue transferida", json={"transfer_reference": "TRX-2"})


def test_settlement_without_bank_account_cannot_be_paid(payouts_api, api_db, market):
    from app.services.payout_service import run_daily_settlements

    _stripe_paid_order(payouts_api, api_db, market)
    backdate(api_db)
    settlement_id = run_daily_settlements(api_db)[0].id
    rejected(payouts_api, api_db, market.superadmin, "PATCH", f"/payouts/settlements/{settlement_id}/paid", 400,
             "La empresa no registró su cuenta bancaria", json={"transfer_reference": "TRX-1"})


def test_summary_shows_pending_balance(payouts_api, api_db, market):
    _stripe_paid_order(payouts_api, api_db, market)
    summary = call(payouts_api, market.staff[0, "administrador"], "GET", "/payouts/summary")
    assert Decimal(str(summary["pending_net_amount"])) == Decimal("22.50")
    assert Decimal(str(summary["platform_fee_percent"])) == 10
