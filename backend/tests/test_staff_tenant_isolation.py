"""CU1: tenant staff management cannot become global identity administration."""
from types import SimpleNamespace

import pytest

from test_catalog_tenant_isolation import catalog
from test_employee_authorization import DENIED, headers, rejected


ROOT = "/api/users"


@pytest.fixture
def staff(api_db, catalog):
    from app.models.user import User
    from app.schemas.enums import GenderEnum, RolEnum
    users = []
    for name, role, tenant, branch in (
        ("Own cashier", RolEnum.cajero, catalog.own.tenant.id, catalog.branches[0].id),
        ("Other cashier", RolEnum.cajero, catalog.foreign.tenant.id, catalog.branches[2].id),
        ("Customer", RolEnum.cliente, None, None),
        ("Platform", RolEnum.superadministrador, None, None),
    ):
        user = User(name=name, email=name.replace(" ", "").lower() + "@example.com",
                    hashed_password="unused", gender=GenderEnum.femenino, rol=role,
                    tenant_id=tenant, branch_id=branch, is_active=True)
        api_db.add(user)
        users.append(user)
    api_db.commit()
    return SimpleNamespace(own=users[0], foreign=users[1], customer=users[2], platform=users[3])


def profile_payload(user, **changes):
    return {"name": "Updated staff", "email": user.email, "gender": "femenino",
            "branch_id": str(user.branch_id) if user.branch_id else None,
            "is_active": True, **changes}


def get_user(api, user_id, auth):
    result = api.get(ROOT + f"/{user_id}", headers=auth)
    assert result.status_code == 200, result.text
    return result.json()["data"]


@pytest.mark.parametrize("target", ["foreign", "customer", "platform"])
@pytest.mark.parametrize("operation", ["read", "role", "branch", "full", "active", "delete"])
def test_admin_cannot_address_foreign_or_global_identity(api, api_db, catalog, staff, target, operation):
    user = getattr(staff, target)
    method, suffix, kwargs = {
        "read": ("GET", "", {}),
        "role": ("PATCH", "/rol", {"json": {"rol": "administrador"}}),
        "branch": ("PATCH", "/branch", {"json": {"branch_id": str(catalog.branches[0].id)}}),
        "full": ("PUT", "", {"json": profile_payload(user)}),
        "active": ("PATCH", "/active", {"json": {"is_active": False}}),
        "delete": ("DELETE", "", {}),
    }[operation]
    rejected(api, api_db, method, ROOT + f"/{user.id}{suffix}", headers(catalog.user),
             404, f"Usuario con id {user.id} no encontrado", **kwargs)
    own_profile = api.get(ROOT + "/me", headers=headers(user))
    assert own_profile.status_code == 200, own_profile.text
    assert own_profile.json()["data"]["name"] == user.name


def test_staff_list_and_count_exclude_other_company_and_global_accounts(api, catalog, staff):
    result = api.get(ROOT + "/", headers=headers(catalog.user))
    assert result.status_code == 200, result.text
    assert result.json()["countData"] == 3
    assert {row["id"] for row in result.json()["data"]} == {
        str(catalog.user.id), str(catalog.own.supplier_user.id), str(staff.own.id)}


@pytest.mark.parametrize("entry", ["create", "role"])
def test_admin_cannot_promote_or_create_platform_administrator(api, api_db, catalog, staff, entry):
    if entry == "create":
        method, path = "POST", ROOT + "/admin"
        payload = {"name": "Escalation", "email": "escalation@example.com", "password": "safe-password",
                   "gender": "femenino", "rol": "superadministrador"}
        # Existing internal-creation policy already excludes platform roles.
        code, message = 400, "Este formulario solo permite crear usuarios internos"
    else:
        method, path = "PATCH", ROOT + f"/{staff.own.id}/rol"
        payload = {"rol": "superadministrador"}
        code, message = 403, DENIED
    rejected(api, api_db, method, path, headers(catalog.user), code, message, json=payload)


@pytest.mark.parametrize("entry", ["create", "role", "branch", "full"])
@pytest.mark.parametrize("invalid", ["foreign", "inactive"])
def test_staff_assignment_rejects_foreign_or_inactive_branch_before_writes(api, api_db, catalog, staff, entry, invalid):
    branch = catalog.branches[2] if invalid == "foreign" else catalog.branches[1]
    if invalid == "inactive":
        branch.is_active = False
        api_db.commit()
    value = str(branch.id)
    if entry == "create":
        method, path = "POST", ROOT + "/admin"
        payload = {"name": "Invalid", "email": "invalid@example.com", "password": "safe-password",
                   "gender": "femenino", "rol": "cajero", "branch_id": value}
    elif entry == "role":
        method, path = "PATCH", ROOT + f"/{staff.own.id}/rol"
        payload = {"rol": "encargado", "branch_id": value}
    elif entry == "branch":
        method, path = "PATCH", ROOT + f"/{staff.own.id}/branch"
        payload = {"branch_id": value}
    else:
        method, path = "PUT", ROOT + f"/{staff.own.id}"
        payload = profile_payload(staff.own, branch_id=value)
    rejected(api, api_db, method, path, headers(catalog.user), 400,
             "La sucursal no existe o está inactiva en esta empresa", json=payload)


def test_admin_preserves_own_staff_create_read_role_branch_update_active_delete(api, catalog, staff):
    auth = headers(catalog.user)
    result = api.post(ROOT + "/admin", headers=auth, json={
        "name": "New cashier", "email": "new-cashier@example.com", "password": "safe-password",
        "gender": "femenino", "rol": "cajero", "branch_id": str(catalog.branches[0].id),
        "tenant_id": str(catalog.foreign.tenant.id)})
    assert result.status_code == 201, result.text
    assert result.json()["message"] == "Usuario creado exitosamente"
    user_id = result.json()["data"]["id"]
    assert get_user(api, user_id, auth)["tenant_id"] == str(catalog.own.tenant.id)
    operations = [
        ("PATCH", "/rol", {"rol": "encargado", "branch_id": str(catalog.branches[0].id)}, "Rol de usuario actualizado exitosamente"),
        ("PATCH", "/branch", {"branch_id": str(catalog.branches[1].id)}, "Sucursal de usuario actualizada exitosamente"),
        ("PUT", "", {"name": "Renamed", "email": "renamed@example.com", "gender": "masculino",
                     "branch_id": str(catalog.branches[1].id), "is_active": True}, "Usuario actualizado exitosamente"),
        ("PATCH", "/active", {"is_active": False}, "Estado de usuario actualizado exitosamente"),
    ]
    for method, suffix, payload, message in operations:
        result = api.request(method, ROOT + f"/{user_id}{suffix}", headers=auth, json=payload)
        assert result.status_code == 200, result.text
        assert result.json()["message"] == message
        stored = get_user(api, user_id, auth)
        for key, value in payload.items():
            assert stored[key] == value
    result = api.delete(ROOT + f"/{user_id}", headers=auth)
    assert result.status_code == 200, result.text
    assert result.json()["message"] == "Usuario eliminado exitosamente"
    assert api.get(ROOT + "/", headers=auth).json()["countData"] == 3


def test_global_customer_keeps_own_profile_update(api, staff):
    auth = headers(staff.customer)
    result = api.put(ROOT + "/me", headers=auth, json={
        "name": "Customer renamed", "email": "customer-renamed@example.com", "gender": "masculino"})
    assert result.status_code == 200, result.text
    assert result.json()["message"] == "Perfil actualizado exitosamente"
    profile = api.get(ROOT + "/me", headers=auth).json()["data"]
    assert (profile["name"], profile["email"], profile["gender"]) == (
        "Customer renamed", "customer-renamed@example.com", "masculino")
    assert (profile["rol"], profile["tenant_id"], profile["branch_id"]) == ("cliente", None, None)
