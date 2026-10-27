import uuid
import pytest
from fastapi.testclient import TestClient

from main import app
from app.models.tenant import Tenant
from app.models.branch import Branch
from app.core.database import SessionLocal

client = TestClient(app)
pytestmark = pytest.mark.usefixtures("seeded_db")  # logs in with backend/seed.py accounts

TENANT_1_ID = "11111111-1111-1111-1111-111111111111"
TENANT_2_ID = "22222222-2222-2222-2222-222222222222"
TENANT_3_ID = "33333333-3333-3333-3333-333333333333"


def test_superadmin_unified_login_and_tenant_crud():
    # 1. Login Superadmin (unificado: solo email + password)
    res = client.post(
        "/api/auth/login",
        json={"email": "superadmin@fashionstore.com", "password": "SuperAdmin2026!"},
    )
    assert res.status_code == 200, res.text
    body = res.json()["data"]
    assert body["user"]["rol"] == "superadministrador"
    assert body["user"]["tenant_id"] is None
    token = body["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Listar tenants
    res_list = client.get("/api/saas/tenants/?limit=100", headers=headers)
    assert res_list.status_code == 200
    tenants = res_list.json()["data"]
    tenant_names = [t["name"] for t in tenants]
    assert "Aura Moda" in tenant_names
    assert "UrbanStyle" in tenant_names
    assert "NovaWear" in tenant_names

    # 2.1. Listar tenants públicos
    res_public = client.get("/api/saas/tenants/public")
    assert res_public.status_code == 200
    public_names = [t["name"] for t in res_public.json()["data"]]
    assert "Aura Moda" in public_names
    assert "UrbanStyle" in public_names
    assert "NovaWear" in public_names

    # 3. Crear nuevo tenant
    new_slug = f"test-brand-{uuid.uuid4().hex[:6]}"
    create_payload = {
        "name": f"Test Brand {uuid.uuid4().hex[:6]}",
        "slug": new_slug,
        "contact_email": f"{new_slug}@testbrand.bo",
        "currency": "BOB",
        "country": "Bolivia",
        "status": "active",
    }
    res_create = client.post("/api/saas/tenants/", json=create_payload, headers=headers)
    assert res_create.status_code == 201
    created_tenant = res_create.json()["data"]
    tenant_id = created_tenant["id"]

    # 4. Obtener detalle de tenant
    res_get = client.get(f"/api/saas/tenants/{tenant_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["data"]["slug"] == new_slug

    # 5. Modificar tenant
    res_patch = client.patch(f"/api/saas/tenants/{tenant_id}", json={"currency": "USD"}, headers=headers)
    assert res_patch.status_code == 200
    assert res_patch.json()["data"]["currency"] == "USD"

    # 6. Cambiar estado a suspended y reactivar
    res_suspend = client.patch(f"/api/saas/tenants/{tenant_id}/status", json={"status": "suspended"}, headers=headers)
    assert res_suspend.status_code == 200
    assert res_suspend.json()["data"]["status"] == "suspended"

    res_reactivate = client.patch(f"/api/saas/tenants/{tenant_id}/status", json={"status": "active"}, headers=headers)
    assert res_reactivate.status_code == 200
    assert res_reactivate.json()["data"]["status"] == "active"


def test_admin_and_cashier_tenant_isolation():
    # 1. Login Admin Aura Moda (Tenant 1)
    res_admin = client.post(
        "/api/auth/login",
        json={"email": "admin.global@fashionstore.bo", "password": "Fashion123!"},
    )
    assert res_admin.status_code == 200
    admin_body = res_admin.json()["data"]
    assert admin_body["user"]["rol"] == "administrador"
    assert admin_body["user"]["tenant_id"] == TENANT_1_ID
    admin_token = admin_body["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. El administrador NO puede acceder a las rutas de Superadmin (/api/saas/tenants)
    res_forbidden = client.get("/api/saas/tenants/", headers=admin_headers)
    assert res_forbidden.status_code == 403

    # 3. El administrador solo ve sucursales de su empresa (Tenant 1)
    res_branches = client.get("/api/branches/", headers=admin_headers)
    assert res_branches.status_code == 200
    branches = res_branches.json()["data"]
    assert len(branches) >= 3

    # Crear una sucursal en Tenant 2 (UrbanStyle) directamente en DB para probar aislamiento
    with SessionLocal() as db:
        branch_t2 = Branch(
            name=f"Sucursal UrbanStyle {uuid.uuid4().hex[:6]}",
            city="Santa Cruz",
            tenant_id=uuid.UUID(TENANT_2_ID),
            is_active=True,
        )
        db.add(branch_t2)
        db.commit()
        db.refresh(branch_t2)
        branch_t2_id = branch_t2.id

    # El admin de Tenant 1 consulta sus sucursales y NO ve la sucursal de Tenant 2
    res_branches_check = client.get("/api/branches/", headers=admin_headers)
    branch_ids = [b["id"] for b in res_branches_check.json()["data"]]
    assert str(branch_t2_id) not in branch_ids

    # El admin de Tenant 1 intenta modificar o eliminar la sucursal de Tenant 2 -> 404 (no encontrada en su empresa)
    res_update_alien = client.put(
        f"/api/branches/{branch_t2_id}",
        json={"name": "Hack Branch", "city": "La Paz", "is_default": False, "is_active": True},
        headers=admin_headers,
    )
    assert res_update_alien.status_code == 404

    res_delete_alien = client.delete(f"/api/branches/{branch_t2_id}", headers=admin_headers)
    assert res_delete_alien.status_code == 404

    # 4. Login Cajera La Paz (Tenant 1)
    res_cashier = client.post(
        "/api/auth/login",
        json={"email": "cajera.lp@fashionstore.bo", "password": "Fashion123!"},
    )
    assert res_cashier.status_code == 200
    cashier_body = res_cashier.json()["data"]
    assert cashier_body["user"]["rol"] == "cajero"
    assert cashier_body["user"]["tenant_id"] == TENANT_1_ID
    assert cashier_body["user"]["branch_id"] is not None
    cashier_token = cashier_body["access_token"]
    cashier_headers = {"Authorization": f"Bearer {cashier_token}"}

    # Cajera no puede gestionar tenants
    assert client.get("/api/saas/tenants/", headers=cashier_headers).status_code == 403

    # Cajera consulta ventas de sucursal -> 200 OK
    res_sales = client.get("/api/sales/branch", headers=cashier_headers)
    assert res_sales.status_code == 200
    assert isinstance(res_sales.json()["data"], list)


def test_global_client_unified_experience():
    # 1. Login cliente global
    res_client = client.post(
        "/api/auth/login",
        json={"email": "cliente01.demo@fashionstore.bo", "password": "Fashion123!"},
    )
    assert res_client.status_code == 200
    client_body = res_client.json()["data"]
    assert client_body["user"]["rol"] == "cliente"
    assert client_body["user"]["tenant_id"] is None
    client_token = client_body["access_token"]
    client_headers = {"Authorization": f"Bearer {client_token}"}

    # 2. Perfil /api/users/me confirma usuario global
    res_me = client.get("/api/users/me", headers=client_headers)
    assert res_me.status_code == 200
    assert res_me.json()["data"]["tenant_id"] is None

    # 3. Cliente puede consultar sucursales públicas
    res_public = client.get("/api/branches/public")
    assert res_public.status_code == 200
    assert len(res_public.json()["data"]) >= 3

    # 4. Cliente puede filtrar sucursales por tenant
    res_filtered = client.get(f"/api/branches/public?tenant_id={TENANT_1_ID}")
    assert res_filtered.status_code == 200
    assert len(res_filtered.json()["data"]) >= 3

    # 5. Cliente NO tiene acceso a endpoints de administración interna
    assert client.get("/api/saas/tenants/", headers=client_headers).status_code == 403
    assert client.get("/api/branches/", headers=client_headers).status_code == 403
