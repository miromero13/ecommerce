"""Real routes/JWTs: each test names the authorization break it detects."""
from uuid import uuid4

import pytest
from sqlalchemy import text


DENIED = "No tienes permisos para acceder a este recurso"


def headers(user, **claims):
    from app.auth.jwt import create_access_token
    payload = dict(sub=str(user.id), rol=user.rol.value,
                   tenant_id=str(user.tenant_id) if user.tenant_id else None,
                   branch_id=str(user.branch_id) if user.branch_id else None)
    return {"Authorization": "Bearer " + create_access_token({**payload, **claims})}


def snapshot(db):
    # SQL snapshot is independent of identity-map state and includes counters.
    return {table: db.execute(text(f"SELECT row_to_json(t)::text FROM {table} t ORDER BY id")).all()
            for table in ("users", "branches", "tenants", "categories")}


def rejected(api, db, method, path, auth, code, message, **kwargs):
    before = snapshot(db)
    result = api.request(method, path, headers=auth, **kwargs)
    assert result.status_code == code, result.text
    assert result.json() == {"statusCode": code, "message": message, "error": "HTTPException"}
    assert snapshot(db) == before


def branch_ids(api, auth):
    result = api.get("/api/branches/", headers=auth)
    assert result.status_code == 200, result.text
    assert result.json()["message"] == "Sucursales obtenidas exitosamente"
    return {row["id"] for row in result.json()["data"]}


def test_old_admin_claim_cannot_mutate_after_demotion(api, api_db, identities):
    from app.schemas.enums import RolEnum
    user, _, branches = identities
    auth = headers(user)
    user.rol = RolEnum.cliente
    user.tenant_id = None
    api_db.commit()
    rejected(api, api_db, "PATCH", f"/api/branches/{branches[0].id}/active", auth,
             403, DENIED, json={"is_active": False})
    profile = api.get("/api/users/me", headers=auth)
    assert profile.status_code == 200
    assert profile.json()["data"]["rol"] == "cliente"
    assert profile.json()["data"]["tenant_id"] is None


def test_old_tenant_claim_cannot_keep_previous_company_scope(api, api_db, identities):
    user, tenants, branches = identities
    auth = headers(user)
    user.tenant_id = tenants[1].id
    api_db.commit()
    assert branch_ids(api, auth) == {str(branches[2].id)}
    rejected(api, api_db, "PATCH", f"/api/branches/{branches[0].id}/active", auth, 404,
             f"Sucursal con id {branches[0].id} no encontrada", json={"is_active": False})


@pytest.mark.parametrize("role", ["cajero", "encargado"])
def test_old_branch_claim_cannot_keep_previous_operational_scope(api, api_db, identities, role):
    from app.schemas.enums import RolEnum
    user, _, branches = identities
    user.rol = RolEnum(role)
    user.branch_id = branches[0].id
    api_db.commit()
    auth = headers(user)
    assert branch_ids(api, auth) == {str(branches[0].id)}
    user.branch_id = branches[1].id
    api_db.commit()
    assert branch_ids(api, auth) == {str(branches[1].id)}


@pytest.mark.parametrize("role", ["administrador", "proveedor", "encargado", "cajero"])
def test_missing_current_tenant_never_becomes_global_employee(api, api_db, identities, role):
    from app.schemas.enums import RolEnum
    user, _, branches = identities
    user.rol = RolEnum(role)
    user.branch_id = branches[0].id
    api_db.commit()
    auth = headers(user)
    user.tenant_id = None
    api_db.commit()
    rejected(api, api_db, "GET", "/api/branches/", auth, 403, "Usuario sin empresa asociada")


@pytest.mark.parametrize("role", ["cajero", "encargado"])
@pytest.mark.parametrize("invalid", ["missing", "mismatched", "inactive"])
def test_invalid_current_branch_never_grants_operational_access(api, api_db, identities, role, invalid):
    from app.schemas.enums import RolEnum
    user, _, branches = identities
    user.rol = RolEnum(role)
    user.branch_id = branches[0].id
    api_db.commit()
    auth = headers(user)
    if invalid == "missing":
        user.branch_id = None
    elif invalid == "mismatched":
        user.branch_id = branches[2].id
    else:
        branches[0].is_active = False
    api_db.commit()
    message = ("Usuario operativo sin sucursal asignada" if invalid == "missing"
               else "La sucursal no existe o está inactiva en esta empresa")
    rejected(api, api_db, "GET", "/api/branches/", auth, 403, message)


@pytest.mark.parametrize("revocation", ["inactive", "deleted"])
def test_revoked_database_identity_cannot_use_signed_token(api, api_db, identities, revocation):
    user, _, branches = identities
    auth = headers(user)
    if revocation == "inactive":
        user.is_active = False
    else:
        api_db.delete(user)
    api_db.commit()
    code, message = ((403, "Usuario inactivo") if revocation == "inactive"
                     else (401, "Usuario no encontrado"))
    rejected(api, api_db, "PATCH", f"/api/branches/{branches[0].id}/active", auth,
             code, message, json={"is_active": False})
    rejected(api, api_db, "GET", "/api/users/me", auth, code, message)


@pytest.mark.parametrize("subject", [None, "not-a-uuid", "", 123, [], str(uuid4())])
def test_invalid_subject_uses_existing_401_contract(api, api_db, identities, subject):
    user, _, _ = identities
    auth = headers(user, sub=subject)
    message = "Usuario no encontrado" if isinstance(subject, str) and len(subject) == 36 else "Token inválido"
    for path in ("/api/users/me", "/api/branches/"):
        rejected(api, api_db, "GET", path, auth, 401, message)


def test_same_tenant_admin_still_reads_and_mutates_own_branch(api, api_db, identities):
    user, _, branches = identities
    auth = headers(user)
    assert branch_ids(api, auth) == {str(branch.id) for branch in branches[:2]}
    result = api.patch(f"/api/branches/{branches[0].id}/active", headers=auth, json={"is_active": False})
    assert result.status_code == 200
    assert result.json()["data"]["is_active"] is False
    assert result.json()["message"] == "Estado de sucursal actualizado exitosamente"
    assert api.get("/api/users/", headers=auth).json()["countData"] == 1


def test_global_customer_keeps_public_browsing_and_own_profile(api, api_db, identities):
    from app.schemas.enums import RolEnum
    user, _, branches = identities
    user.rol = RolEnum.cliente
    user.tenant_id = None
    api_db.commit()
    auth = headers(user)
    for credentials in ({}, auth):
        result = api.get("/api/branches/public", headers=credentials)
        assert result.status_code == 200
        assert {row["id"] for row in result.json()["data"]} == {str(b.id) for b in branches}
        result = api.get("/api/catalog/products", headers=credentials)
        assert result.status_code == 200
        assert result.json() == {"statusCode": 200, "message": "Productos obtenidos exitosamente", "data": []}
    profile = api.get("/api/users/me", headers=auth)
    assert profile.status_code == 200
    assert profile.json()["data"]["tenant_id"] is None
    assert profile.json()["data"]["id"] == str(user.id)
    rejected(api, api_db, "GET", "/api/branches/", auth, 403, DENIED)


def test_global_superadmin_keeps_existing_platform_management(api, api_db, identities):
    from app.schemas.enums import RolEnum
    user, _, branches = identities
    user.rol = RolEnum.superadministrador
    user.tenant_id = None
    api_db.commit()
    auth = headers(user)
    assert branch_ids(api, auth) == {str(branch.id) for branch in branches}
    assert api.get("/api/saas/tenants/", headers=auth).json()["countData"] == 2
    created = api.post("/api/saas/tenants/", headers=auth, json={
        "name": "Gamma", "slug": "gamma", "contact_email": "gamma@example.com"})
    assert created.status_code == 201, created.text
    tid = created.json()["data"]["id"]
    assert api.get(f"/api/saas/tenants/{tid}", headers=auth).json()["data"]["name"] == "Gamma"
    updated = api.patch(f"/api/saas/tenants/{tid}", headers=auth, json={"name": "Gamma Updated"})
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "Gamma Updated"
    status = api.patch(f"/api/saas/tenants/{tid}/status", headers=auth, json={"status": "suspended"})
    assert status.status_code == 200
    assert status.json()["data"]["status"] == "suspended"
    # No DELETE exists in this public contract; do not invent one.
    rejected(api, api_db, "PATCH", f"/api/branches/{branches[0].id}/active", auth,
             403, DENIED, json={"is_active": False})
