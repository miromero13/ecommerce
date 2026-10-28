"""CU1: the superadmin enters a company's administrative panel as its administrator."""
import pytest

from test_employee_authorization import DENIED, branch_ids, headers, rejected


ADMIN = {"name": "Ana Admin", "email": "ana@gamma.com", "password": "secreta123", "gender": "femenino"}


@pytest.fixture
def superadmin(api_db, identities):
    from app.models.user import User
    from app.schemas.enums import GenderEnum, RolEnum

    user = User(name="Root", email="root@example.com", hashed_password="unused", gender=GenderEnum.masculino,
                rol=RolEnum.superadministrador, tenant_id=None, is_active=True)
    api_db.add(user)
    api_db.commit()
    return user


def test_superadmin_enters_the_company_panel_as_its_administrator(api, api_db, identities, superadmin):
    from app.auth.jwt import decode_access_token

    admin, tenants, branches = identities
    result = api.post(f"/api/saas/tenants/{tenants[0].id}/panel-session", headers=headers(superadmin))
    assert result.status_code == 200, result.text
    body = result.json()
    assert body["message"] == "Ingresaste al panel de Alpha"
    session = body["data"]
    assert session["user"]["id"] == str(admin.id) and session["user"]["rol"] == "administrador"
    claims = decode_access_token(session["access_token"])
    assert claims["impersonated_by"] == str(superadmin.id) and claims["tenant_id"] == str(tenants[0].id)
    # Full administrator access, limited to that company.
    panel = {"Authorization": "Bearer " + session["access_token"]}
    assert branch_ids(api, panel) == {str(branches[0].id), str(branches[1].id)}


def test_company_without_administrator_asks_to_register_one(api, api_db, identities, superadmin):
    _, tenants, _ = identities
    auth = headers(superadmin)
    rejected(api, api_db, "POST", f"/api/saas/tenants/{tenants[1].id}/panel-session", auth, 409,
             "La empresa no tiene un administrador activo. Regístralo desde el detalle de la empresa.")
    registered = api.post(f"/api/saas/tenants/{tenants[1].id}/admin", headers=auth, json=ADMIN)
    assert registered.status_code == 201, registered.text
    assert registered.json()["data"]["has_admin"] is True
    assert api.post(f"/api/saas/tenants/{tenants[1].id}/panel-session", headers=auth).status_code == 200
    rejected(api, api_db, "POST", f"/api/saas/tenants/{tenants[1].id}/admin", auth, 400,
             "La empresa ya tiene un administrador activo", json={**ADMIN, "email": "otra@beta.com"})


def test_suspended_company_and_non_superadmins_cannot_open_a_panel(api, api_db, identities, superadmin):
    from app.schemas.enums import TenantStatusEnum

    admin, tenants, _ = identities
    rejected(api, api_db, "POST", f"/api/saas/tenants/{tenants[1].id}/panel-session", headers(admin), 403, DENIED)
    tenants[0].status = TenantStatusEnum.suspended
    api_db.commit()
    rejected(api, api_db, "POST", f"/api/saas/tenants/{tenants[0].id}/panel-session", headers(superadmin), 400,
             "La empresa está suspendida: actívala para entrar a su panel")
