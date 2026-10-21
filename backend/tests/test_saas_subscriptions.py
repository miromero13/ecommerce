import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from main import app
from app.core.database import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.models.branch import Branch
from app.schemas.branch_schema import BranchCreate
from app.services.branch_service import create_branch
from app.services.subscription_service import get_active_subscription


@pytest.fixture
def client():
    return TestClient(app)


def test_list_saas_plans(client):
    response = client.get("/api/saas/plans")
    assert response.status_code == 200
    data = response.json()
    assert data["statusCode"] == 200
    assert len(data["data"]) == 3
    plan_ids = [p["id"] for p in data["data"]]
    assert "plan_basic" in plan_ids
    assert "plan_pro" in plan_ids
    assert "plan_enterprise" in plan_ids

    # Check features in Pro and Enterprise
    pro_plan = next(p for p in data["data"] if p["id"] == "plan_pro")
    assert "virtual_try_on_2d" in pro_plan["features"]
    assert "ai_text_reports" in pro_plan["features"]

    enterprise_plan = next(p for p in data["data"] if p["id"] == "plan_enterprise")
    assert "virtual_try_on_3d_ar" in enterprise_plan["features"]
    assert "ai_ml_smart_reports" in enterprise_plan["features"]


def test_purchase_simulated_creates_tenant_admin_and_subscription(client):
    unique_suffix = uuid4().hex[:8]
    company_name = f"Test Brand {unique_suffix}"
    admin_email = f"admin_{unique_suffix}@testbrand.com"

    payload = {
        "company_name": company_name,
        "slug": f"brand-{unique_suffix}",
        "country": "Bolivia",
        "currency": "BOB",
        "admin_name": f"Admin {unique_suffix}",
        "admin_email": admin_email,
        "plan_id": "plan_pro",
        "billing_cycle": "monthly",
        "card_number": "4242424242424242",
        "card_holder": "Titular Test",
        "card_exp": "12/28",
        "card_cvv": "123",
    }

    res = client.post("/api/saas/subscriptions/purchase-simulated", json=payload)
    assert res.status_code == 201
    res_data = res.json()
    assert res_data["statusCode"] == 201
    assert "Suscripción activada con éxito" in res_data["message"]
    tenant_id = res_data["data"]["tenant_id"]

    # Verify DB state
    db = SessionLocal()
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    assert tenant is not None
    assert tenant.name == company_name

    user = db.query(User).filter(User.email == admin_email).first()
    assert user is not None
    assert user.rol.value == "administrador"
    assert str(user.tenant_id) == tenant_id

    sub = get_active_subscription(db, tenant.id)
    assert sub is not None
    assert sub.plan_id == "plan_pro"
    assert sub.status.value == "active"
    db.close()


def test_superadmin_creates_tenant_with_cash_subscription(client):
    # 1. Login superadmin
    login_res = client.post(
        "/api/auth/login",
        json={"email": "superadmin@fashionstore.com", "password": "SuperAdmin2026!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    unique_suffix = uuid4().hex[:8]
    payload = {
        "name": f"Direct Cash Tenant {unique_suffix}",
        "slug": f"cash-{unique_suffix}",
        "contact_email": f"cashadmin_{unique_suffix}@fashionstore.bo",
        "country": "Bolivia",
        "currency": "BOB",
        "admin_name": f"Cash Admin {unique_suffix}",
        "plan_id": "plan_basic",
        "billing_cycle": "yearly",
        "payment_method": "cash",
    }

    res = client.post("/api/saas/tenants/with-subscription", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["statusCode"] == 201
    assert "creadas exitosamente" in data["message"]
    tenant_id = data["data"]["tenant_id"]

    # 2. Get current subscription for this tenant
    sub_res = client.get(f"/api/saas/subscriptions/current?tenant_id={tenant_id}", headers=headers)
    assert sub_res.status_code == 200
    sub_data = sub_res.json()["data"]
    assert sub_data["has_active_subscription"] is True
    assert sub_data["plan"]["id"] == "plan_basic"
    assert sub_data["subscription"]["payment_method"] == "cash"
    assert sub_data["subscription"]["billing_cycle"] == "yearly"


def test_branch_quota_limit_exceeded_raises_403(client):
    # Tenant 3 (NovaWear) has plan_basic (max 2 branches)
    # Let's create a temporary tenant with plan_basic and test branch creation limit
    unique_suffix = uuid4().hex[:8]
    payload = {
        "company_name": f"Quota Brand {unique_suffix}",
        "slug": f"quota-{unique_suffix}",
        "admin_name": "Quota Admin",
        "admin_email": f"quota_{unique_suffix}@brand.bo",
        "plan_id": "plan_basic",
        "billing_cycle": "monthly",
    }
    res = client.post("/api/saas/subscriptions/purchase-simulated", json=payload)
    assert res.status_code == 201
    tenant_id = res.json()["data"]["tenant_id"]

    db = SessionLocal()
    from uuid import UUID
    t_uuid = UUID(tenant_id)

    # Plan basic allows max 2 branches
    # Branch 1: OK
    b1 = create_branch(db, BranchCreate(name="Branch 1", city="La Paz", is_default=True), tenant_id=t_uuid)
    assert b1 is not None

    # Branch 2: OK
    b2 = create_branch(db, BranchCreate(name="Branch 2", city="Cochabamba", is_default=False), tenant_id=t_uuid)
    assert b2 is not None

    # Branch 3: Must raise HTTPException 403
    with pytest.raises(Exception) as exc_info:
        create_branch(db, BranchCreate(name="Branch 3", city="Santa Cruz", is_default=False), tenant_id=t_uuid)
    assert "Límite de sucursales alcanzado" in str(exc_info.value)
    db.close()


def test_login_with_random_generated_password_after_onboarding(client, monkeypatch):
    captured_credentials = {}

    async def fake_send_welcome(to_email, admin_name, tenant_name, plan_name, password, **kwargs):
        captured_credentials["email"] = to_email
        captured_credentials["password"] = password
        return True

    from app.services.email_service import email_service
    monkeypatch.setattr(email_service, "send_welcome_credentials_email", fake_send_welcome)

    unique_suffix = uuid4().hex[:8]
    company_name = f"AutoLogin Brand {unique_suffix}"
    admin_email = f"admin_{unique_suffix}@autologin.bo"

    payload = {
        "company_name": company_name,
        "slug": f"autologin-{unique_suffix}",
        "admin_name": "Valeria AutoLogin",
        "admin_email": admin_email,
        "plan_id": "plan_enterprise",
        "billing_cycle": "monthly",
    }

    res = client.post("/api/saas/subscriptions/purchase-simulated", json=payload)
    assert res.status_code == 201

    assert captured_credentials["email"] == admin_email
    generated_pwd = captured_credentials["password"]
    assert len(generated_pwd) >= 12

    # Attempt login with the generated credentials
    login_res = client.post(
        "/api/auth/login",
        json={"email": admin_email, "password": generated_pwd},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()["data"]
    assert login_data["user"]["rol"] == "administrador"
    assert login_data["user"]["email"] == admin_email
    assert login_data["access_token"] is not None

