from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.rbac import Permission, Role
from app.models.user import User
from app.schemas.enums import RolEnum
from app.schemas.rbac_schema import RoleCreate, RoleUpdate, UserRolesAssign


PERMISSIONS_CATALOG = [
    ("inventory:read", "inventory", "Consultar inventario y existencias"),
    ("inventory:transfer", "inventory", "Efectuar traspasos entre sucursales"),
    ("inventory:adjust", "inventory", "Ajustar existencias de inventario"),
    ("sales:create", "sales", "Registrar ventas en caja"),
    ("sales:read", "sales", "Consultar historial de ventas"),
    ("reports:read", "reports", "Consultar y exportar reportes"),
    ("reports:ai", "reports", "Generar reportes inteligentes con IA"),
    ("catalog:manage", "catalog", "Administrar productos, categorías y variantes"),
    ("users:manage", "users", "Administrar empleados y usuarios"),
    ("rbac:manage", "rbac", "Administrar roles y permisos"),
    ("replenishment:manage", "replenishment", "Gestionar solicitudes de reabastecimiento"),
    ("promotions:manage", "promotions", "Administrar cupones y promociones"),
    ("orders:manage", "orders", "Gestionar pedidos de clientes"),
    ("reservations:manage", "reservations", "Gestionar reservas de prendas"),
]

ALL_PERMISSION_NAMES = [p[0] for p in PERMISSIONS_CATALOG]
# Company staff that may receive custom roles (administrators already have every permission).
ASSIGNABLE_BASE_ROLES = {RolEnum.encargado, RolEnum.cajero, RolEnum.proveedor}

DEFAULT_ROLE_PERMISSIONS: dict[RolEnum, list[str]] = {
    RolEnum.superadministrador: ALL_PERMISSION_NAMES,
    RolEnum.administrador: ALL_PERMISSION_NAMES,
    RolEnum.encargado: [
        "inventory:read",
        "inventory:transfer",
        "inventory:adjust",
        "orders:manage",
        "reservations:manage",
        "replenishment:manage",
        "promotions:manage",
        "sales:read",
        "reports:read",
    ],
    RolEnum.cajero: [
        "sales:create",
        "sales:read",
        "inventory:read",
        "reservations:manage",
        "orders:manage",
    ],
    RolEnum.proveedor: [
        "replenishment:manage",
        "catalog:manage",
    ],
    RolEnum.cliente: [
        "reservations:manage",
        "orders:manage",
    ],
    RolEnum.delivery: [
        "orders:manage",
    ],
}


def seed_rbac_if_empty(db: Session) -> None:
    """Ensure catalog permissions and system roles are populated."""
    existing_perms = {p.name: p for p in db.query(Permission).all()}
    for name, module, desc in PERMISSIONS_CATALOG:
        if name not in existing_perms:
            p = Permission(name=name, module=module, description=desc)
            db.add(p)
            existing_perms[name] = p
    db.flush()

    for base_rol, perm_names in DEFAULT_ROLE_PERMISSIONS.items():
        role = (
            db.query(Role)
            .filter(Role.is_system.is_(True), Role.base_rol == base_rol)
            .first()
        )
        if not role:
            role = Role(
                code=base_rol.value,
                name=base_rol.value.capitalize(),
                base_rol=base_rol,
                is_system=True,
                tenant_id=None,
            )
            role.permissions = [existing_perms[pn] for pn in perm_names if pn in existing_perms]
            db.add(role)
    db.commit()


def list_permissions(db: Session) -> list[Permission]:
    seed_rbac_if_empty(db)
    return db.query(Permission).order_by(Permission.module.asc(), Permission.name.asc()).all()


def list_roles(db: Session, tenant_id: UUID | None) -> list[Role]:
    seed_rbac_if_empty(db)
    query = db.query(Role).options(joinedload(Role.permissions))
    if tenant_id:
        query = query.filter((Role.tenant_id == tenant_id) | (Role.tenant_id.is_(None)))
    else:
        query = query.filter(Role.tenant_id.is_(None))
    return query.order_by(Role.is_system.desc(), Role.name.asc()).all()


def create_role(db: Session, tenant_id: UUID, data: RoleCreate) -> Role:
    clean_name = data.name.strip()
    clean_code = data.code.strip().lower()

    if not data.permission_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe asignar al menos un permiso al rol",
        )

    # Check for duplicate code in tenant
    existing = (
        db.query(Role)
        .filter(Role.tenant_id == tenant_id, Role.code == clean_code)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El código del rol ya existe en la organización",
        )

    permissions = db.query(Permission).filter(Permission.id.in_(data.permission_ids)).all()
    if len(permissions) != len(set(data.permission_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uno o más permisos especificados no existen",
        )

    role = Role(
        tenant_id=tenant_id,
        code=clean_code,
        name=clean_name,
        base_rol=None,
        is_system=False,
    )
    role.permissions = permissions
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def update_role(db: Session, tenant_id: UUID, role_id: UUID, data: RoleUpdate) -> Role:
    role = (
        db.query(Role)
        .options(joinedload(Role.permissions))
        .filter(Role.id == role_id)
        .first()
    )
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado",
        )

    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden modificar roles del sistema",
        )

    if role.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado",
        )

    if data.name is not None:
        role.name = data.name.strip()

    if data.permission_ids is not None:
        if len(data.permission_ids) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe asignar al menos un permiso al rol",
            )
        permissions = db.query(Permission).filter(Permission.id.in_(data.permission_ids)).all()
        if len(permissions) != len(set(data.permission_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uno o más permisos especificados no existen",
            )
        role.permissions = permissions

    db.commit()
    db.refresh(role)
    return role


def assign_user_roles(
    db: Session,
    current_tenant_id: UUID | None,
    user_id: UUID,
    data: UserRolesAssign,
) -> list[Role]:
    user = db.query(User).options(joinedload(User.custom_roles)).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    # Only a company's own staff get custom roles: never customers, platform drivers,
    # administrators or another company's employees.
    if user.rol not in ASSIGNABLE_BASE_ROLES or user.tenant_id is None or (
            current_tenant_id is not None and user.tenant_id != current_tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo se pueden asignar roles al personal de tu empresa",
        )

    if not data.role_ids:
        user.custom_roles = []
        db.commit()
        return []

    roles = db.query(Role).filter(Role.id.in_(data.role_ids)).all()
    if len(roles) != len(set(data.role_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uno o más roles no pertenecen a tu organización o no existen",
        )

    # Custom roles must belong to the employee's own company (system roles are not assignable).
    if any(r.is_system or r.tenant_id != user.tenant_id for r in roles):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uno o más roles no pertenecen a tu organización o no existen",
        )

    user.custom_roles = roles
    db.commit()
    return roles


def effective_permissions(db: Session, user: User) -> list[str]:
    """Effective permissions (CU3):

    - Superadministrador and administrador always have every permission.
    - An employee with custom roles of their company gets ONLY those roles' permissions,
      so a restrictive profile really restricts (custom roles replace the base role).
    - Otherwise the base role's default permissions apply.
    """
    if user.rol in [RolEnum.administrador, RolEnum.superadministrador]:
        return sorted(ALL_PERMISSION_NAMES)

    custom = [role for role in user.custom_roles if role.tenant_id is not None and role.tenant_id == user.tenant_id]
    if custom:
        return sorted({permission.name for role in custom for permission in role.permissions})

    perms: set[str] = set()

    # 1. Base system role permissions
    base_perms = DEFAULT_ROLE_PERMISSIONS.get(user.rol, [])
    perms.update(base_perms)

    # Also check if system role in DB has extra permissions
    system_role = (
        db.query(Role)
        .options(joinedload(Role.permissions))
        .filter(Role.is_system.is_(True), Role.base_rol == user.rol)
        .first()
    )
    if system_role:
        for p in system_role.permissions:
            perms.add(p.name)

    return sorted(perms)
