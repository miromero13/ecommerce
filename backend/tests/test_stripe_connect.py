"""D2: each company is paid into its own Stripe Connect account (Stripe is faked)."""
from types import SimpleNamespace

import pytest

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_marketplace_transactions import add, call, market, market_api, rejected  # noqa: F401


@pytest.fixture
def fake_stripe(monkeypatch, market_api):
    import stripe
    from app.core.config import settings
    from app.routes import stripe_connect_routes

    market_api.app.include_router(stripe_connect_routes.router, prefix="/api")
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_fake")
    calls = SimpleNamespace(accounts=[], intents=[], charges_enabled=True)

    def create_account(**kwargs):
        calls.accounts.append(kwargs)
        return SimpleNamespace(id=f"acct_{len(calls.accounts)}")

    def create_intent(**kwargs):
        calls.intents.append(kwargs)
        return SimpleNamespace(id=f"pi_{len(calls.intents)}", client_secret="secret")

    monkeypatch.setattr(stripe.Account, "create", create_account)
    monkeypatch.setattr(stripe.Account, "retrieve", lambda account_id: SimpleNamespace(
        id=account_id, charges_enabled=calls.charges_enabled))
    monkeypatch.setattr(stripe.AccountLink, "create", lambda **kwargs: SimpleNamespace(
        url=f"https://connect.stripe.test/{kwargs['account']}"))
    monkeypatch.setattr(stripe.PaymentIntent, "create", create_intent)
    return calls


def connect(api, admin):
    return call(api, admin, "POST", "/saas/stripe-connect/onboarding-link",
                json={"return_url": "http://localhost:4200/app/admin/subscription"})


def test_onboarding_creates_one_account_per_company(market_api, api_db, market, fake_stripe):
    admin = market.staff[0, "administrador"]
    first, second = connect(market_api, admin), connect(market_api, admin)

    assert first["url"] == second["url"] == "https://connect.stripe.test/acct_1"
    assert len(fake_stripe.accounts) == 1
    assert fake_stripe.accounts[0]["metadata"] == {"tenant_id": str(market.own.tenant.id)}


def test_status_refreshes_charges_enabled_from_stripe(market_api, api_db, market, fake_stripe):
    admin = market.staff[0, "administrador"]
    assert call(market_api, admin, "GET", "/saas/stripe-connect/status")["connected"] is False
    connect(market_api, admin)
    status = call(market_api, admin, "GET", "/saas/stripe-connect/status")
    assert status == {"connected": True, "charges_enabled": True, "account_id": "acct_1"}


def test_card_checkout_requires_company_online_payments(market_api, api_db, market, fake_stripe):
    add(market_api, market)
    rejected(market_api, api_db, market.customer, "POST", "/payments/stripe/checkout", 400,
             "La empresa aún no habilitó pagos en línea",
             json={"pickup_branch_id": str(market.branches[0].id)})
    assert fake_stripe.intents == []


def test_card_payment_is_routed_to_the_company_account(market_api, api_db, market, fake_stripe):
    tenant = market.own.tenant
    tenant.stripe_account_id, tenant.stripe_charges_enabled, tenant.platform_fee_percent = "acct_own", True, 10
    api_db.commit()
    add(market_api, market)

    call(market_api, market.customer, "POST", "/payments/stripe/checkout", 201,
         json={"pickup_branch_id": str(market.branches[0].id)})

    intent = fake_stripe.intents[0]
    assert intent["transfer_data"] == {"destination": "acct_own"}
    assert intent["application_fee_amount"] == intent["amount"] // 10


def test_account_updated_webhook_enables_online_payments(api_db, market):
    from app.services.order_service import process_stripe_event

    market.own.tenant.stripe_account_id = "acct_hook"
    api_db.commit()
    process_stripe_event(api_db, {"id": "evt_1", "type": "account.updated",
                                  "data": {"object": {"id": "acct_hook", "charges_enabled": True}}})
    api_db.refresh(market.own.tenant)
    assert market.own.tenant.stripe_charges_enabled is True
