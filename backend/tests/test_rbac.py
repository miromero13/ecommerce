import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.models.rbac import Permission, Role
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.enums import RolEnum, GenderEnum, TenantStatusEnum
from app.schemas.rbac_schema import RoleCreate, RoleUpdate, UserRolesAssign
from app.services.rbac_service import (
    ALL_PERMISSION_NAMES,
    assign_user_roles,
    create_role,
    effective_permissions,
    list_permissions,
    list_roles,
    seed_rbac_if_empty,
    update_role,
)
from app.auth.dependencies import require_permission
from main import app

# These tests use SessionLocal on the guarded test DB, so they need its migrated schema.
pytestmark = pytest.mark.usefixtures("seeded_db")


def test_seed_and_list_permissions():
    with SessionLocal() as db:
        seed_rbac_if_empty(db)
        perms = list_permissions(db)
        assert len(perms) >= 14
        names = {p.name for p in perms}
        assert "inventory:read" in names
        assert "inventory:transfer" in names
        assert "sales:create" in names
        assert "rbac:manage" in names


def test_effective_permissions_for_administrador():
    with SessionLocal() as db:
        admin_user = SimpleNamespace(
            id=uuid.uuid4(),
            rol=RolEnum.administrador,
            tenant_id=uuid.uuid4(),
            custom_roles=[],
        )
        perms = effective_permissions(db, admin_user)
        assert sorted(perms) == sorted(ALL_PERMISSION_NAMES)
        assert "rbac:manage" in perms
        assert "inventory:transfer" in perms


def test_effective_permissions_for_cajero_without_transfer():
    with SessionLocal() as db:
        seed_rbac_if_empty(db)
        cajero_user = SimpleNamespace(
            id=uuid.uuid4(),
            rol=RolEnum.cajero,
            tenant_id=uuid.uuid4(),
            custom_roles=[],
        )
        perms = effective_permissions(db, cajero_user)
        assert "sales:create" in perms
        assert "inventory:read" in perms
        assert "inventory:transfer" not in perms
        assert "rbac:manage" not in perms


def test_create_custom_role_and_uniqueness():
    with SessionLocal() as db:
        seed_rbac_if_empty(db)
        # Create a test tenant
        tenant_id = uuid.uuid4()
        tenant = Tenant(
            id=tenant_id,
            name=f"RBAC Tenant {tenant_id.hex[:8]}",
            slug=f"rbac-{tenant_id.hex}",
            contact_email=f"admin-{tenant_id.hex[:8]}@example.com",
            currency="BOB",
            country="BO",
            status=TenantStatusEnum.active,
        )
        db.add(tenant)
        db.commit()

        try:
            perms = list_permissions(db)
            perm_map = {p.name: p.id for p in perms}

            # 1. Create custom role
            role_data = RoleCreate(
                name="Asistente de Ventas",
                code="sales_assistant",
                permission_ids=[perm_map["sales:read"], perm_map["inventory:read"]],
            )
            role = create_role(db, tenant.id, role_data)
            assert role.id is not None
            assert role.code == "sales_assistant"
            assert len(role.permissions) == 2

            # 2. Duplicate code in same tenant raises 409
            with pytest.raises(HTTPException) as exc_info:
                create_role(db, tenant.id, role_data)
            assert exc_info.value.status_code == 409
            assert exc_info.value.detail == "El código del rol ya existe en la organización"

            # 3. Empty permissions raises 400
            with pytest.raises(Exception):
                RoleCreate(name="Vacio", code="empty", permission_ids=[])

            # 4. Update custom role
            update_data = RoleUpdate(name="Asistente Senior")
            updated = update_role(db, tenant.id, role.id, update_data)
            assert updated.name == "Asistente Senior"
        finally:
            db.rollback()
            t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if t:
                db.delete(t)
                db.commit()


def test_cannot_modify_system_role():
    with SessionLocal() as db:
        seed_rbac_if_empty(db)
        system_role = (
            db.query(Role)
            .filter(Role.is_system.is_(True), Role.code == "administrador")
            .first()
        )
        assert system_role is not None

        with pytest.raises(HTTPException) as exc_info:
            update_role(
                db,
                tenant_id=uuid.uuid4(),
                role_id=system_role.id,
                data=RoleUpdate(name="Nuevo"),
            )
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "No se pueden modificar roles del sistema"


def test_assign_custom_role_grants_extra_permissions():
    with SessionLocal() as db:
        seed_rbac_if_empty(db)
        tenant_id = uuid.uuid4()
        tenant = Tenant(
            id=tenant_id,
            name=f"RBAC Tenant 2 {tenant_id.hex[:8]}",
            slug=f"rbac-2-{tenant_id.hex}",
            contact_email=f"admin2-{tenant_id.hex[:8]}@example.com",
            currency="BOB",
            country="BO",
            status=TenantStatusEnum.active,
        )
        db.add(tenant)
        db.commit()

        try:
            perms = list_permissions(db)
            perm_map = {p.name: p.id for p in perms}

            # Role that grants inventory:transfer to someone who doesn't have it
            role_data = RoleCreate(
                name="Transfer Specialist",
                code="transfer_spec",
                permission_ids=[perm_map["inventory:transfer"]],
            )
            custom_role = create_role(db, tenant.id, role_data)

            # Create a cajero user in this tenant
            test_user = User(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                name="Cajero Test",
                email=f"cajero-{uuid.uuid4().hex[:8]}@example.com",
                hashed_password="hash",
                gender=GenderEnum.masculino,
                rol=RolEnum.cajero,
                is_active=True,
            )
            db.add(test_user)
            db.commit()

            # Before assignment: cajero does NOT have inventory:transfer
            before_perms = effective_permissions(db, test_user)
            assert "inventory:transfer" not in before_perms

            # Assign role
            assign_user_roles(
                db,
                current_tenant_id=tenant.id,
                user_id=test_user.id,
                data=UserRolesAssign(role_ids=[custom_role.id]),
            )

            # Reload user with custom_roles
            db.refresh(test_user)

            # After assignment the custom role REPLACES the base cashier permissions (CU3).
            after_perms = effective_permissions(db, test_user)
            assert after_perms == ["inventory:transfer"]
        finally:
            db.rollback()
            t = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if t:
                db.delete(t)
                db.commit()


def test_require_permission_raises_403_when_lacking_permission():
    with SessionLocal() as db:
        cajero_user = SimpleNamespace(
            id=uuid.uuid4(),
            rol=RolEnum.cajero,
            tenant_id=uuid.uuid4(),
            custom_roles=[],
        )
        dep = require_permission("inventory:transfer")
        with pytest.raises(HTTPException) as exc_info:
            dep(payload={"sub": str(cajero_user.id)}, user=cajero_user, db=db)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "No tienes permisos suficientes para realizar esta acción"


def _tenant_with(db, *roles):
    tenant_id = uuid.uuid4()
    db.add(Tenant(id=tenant_id, name=f"RBAC {tenant_id.hex[:8]}", slug=f"rbac-{tenant_id.hex}",
                  contact_email=f"rbac-{tenant_id.hex[:8]}@example.com", currency="BOB", country="BO",
                  status=TenantStatusEnum.active))
    users = [User(id=uuid.uuid4(), tenant_id=tenant_id if role != RolEnum.cliente else None, name=role.value,
                  email=f"{role.value}-{uuid.uuid4().hex[:8]}@example.com", hashed_password="hash",
                  gender=GenderEnum.femenino, rol=role, is_active=True) for role in roles]
    db.add_all(users)
    db.commit()
    return tenant_id, users


def _cleanup(db, *tenant_ids):
    db.rollback()
    for tenant_id in tenant_ids:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if tenant:
            db.delete(tenant)
    db.commit()


def test_restrictive_custom_role_removes_base_permissions():
    """CU3 verification: a restrictive profile blocks what the base role allowed."""
    with SessionLocal() as db:
        seed_rbac_if_empty(db)
        tenant_id, (manager,) = _tenant_with(db, RolEnum.encargado)
        try:
            assert "inventory:transfer" in effective_permissions(db, manager)
            perm_map = {p.name: p.id for p in list_permissions(db)}
            read_only = create_role(db, tenant_id, RoleCreate(name="Solo lectura", code="read_only",
                                                              permission_ids=[perm_map["inventory:read"]]))
            assign_user_roles(db, current_tenant_id=tenant_id, user_id=manager.id,
                              data=UserRolesAssign(role_ids=[read_only.id]))
            db.refresh(manager)
            assert effective_permissions(db, manager) == ["inventory:read"]
            with pytest.raises(HTTPException) as denied:
                require_permission("inventory:transfer")(payload={}, user=manager, db=db)
            assert denied.value.status_code == 403
        finally:
            _cleanup(db, tenant_id)


@pytest.mark.parametrize("target", ["other_company", "customer", "administrator"])
def test_roles_are_only_assigned_to_own_company_staff(target):
    with SessionLocal() as db:
        seed_rbac_if_empty(db)
        own, (cashier,) = _tenant_with(db, RolEnum.cajero)
        other, (foreign_cashier, customer, admin) = _tenant_with(db, RolEnum.cajero, RolEnum.cliente, RolEnum.administrador)
        try:
            perm_id = {p.name: p.id for p in list_permissions(db)}["inventory:read"]
            role = create_role(db, own, RoleCreate(name="Lectura", code="lectura", permission_ids=[perm_id]))
            user = {"other_company": foreign_cashier, "customer": customer, "administrator": admin}[target]
            with pytest.raises(HTTPException) as denied:
                assign_user_roles(db, current_tenant_id=own, user_id=user.id, data=UserRolesAssign(role_ids=[role.id]))
            assert denied.value.status_code == 403
            assert denied.value.detail == "Solo se pueden asignar roles al personal de tu empresa"
        finally:
            _cleanup(db, own, other)
