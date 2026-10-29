"""CU2: tenants listed only when subscribed, with their plan, and the payment history of each company."""
import pytest

from test_employee_authorization import headers


@pytest.fixture
def subs_api(api):
    from app.routes import subscription_routes

    api.app.include_router(subscription_routes.router, prefix="/api")
    return api


@pytest.fixture
def superadmin(api_db, identities):
    from app.models.user import User
    from app.schemas.enums import GenderEnum, RolEnum

    user = User(name="Root", email="root@example.com", hashed_password="unused", gender=GenderEnum.masculino,
                rol=RolEnum.superadministrador, tenant_id=None, is_active=True)
    api_db.add(user)
    api_db.commit()
    return user


def test_tenant_list_only_shows_subscribed_companies_with_their_plan(subs_api, api_db, identities, superadmin):
    auth = headers(superadmin)
    created = subs_api.post("/api/saas/tenants/", headers=auth, json={
        "name": "Sin Plan", "slug": "sin-plan", "contact_email": "s@sinplan.com"})
    assert created.status_code == 201, created.text
    listed = subs_api.get("/api/saas/tenants/", headers=auth).json()
    assert listed["countData"] == 2
    assert {row["name"]: row["plan_name"] for row in listed["data"]} == {"Alpha": "Enterprise", "Beta": "Enterprise"}


def test_plan_change_appears_in_the_payment_history(subs_api, api_db, identities, superadmin):
    admin, tenants, _ = identities
    history = subs_api.get("/api/saas/subscriptions/history", headers=headers(admin))
    assert history.status_code == 200, history.text
    assert history.json()["message"] == "Historial de pagos obtenido exitosamente"
    assert [(row["plan_name"], row["status"]) for row in history.json()["data"]] == [("Enterprise", "Vigente")]

    changed = subs_api.post("/api/saas/subscriptions/change-plan", headers=headers(admin),
                            json={"plan_id": "plan_basic", "billing_cycle": "monthly"})
    assert changed.status_code == 200, changed.text
    rows = subs_api.get("/api/saas/subscriptions/history", headers=headers(admin)).json()["data"]
    assert [(r["plan_name"], r["status"], r["amount"], r["payment_method_label"]) for r in rows][0] == (
        "Básico", "Vigente", 49.0, "Tarjeta (simulada)")
    assert rows[1]["plan_name"] == "Enterprise" and rows[1]["status"] == "Reemplazado"

    # The superadmin sees any company's history; it must say which one.
    other = subs_api.get("/api/saas/subscriptions/history", headers=headers(superadmin), params={"tenant_id": str(tenants[1].id)})
    assert [row["plan_name"] for row in other.json()["data"]] == ["Enterprise"]
    assert subs_api.get("/api/saas/subscriptions/history", headers=headers(superadmin)).status_code == 400
