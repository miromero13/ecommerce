"""Add RBAC permissions, roles, role_permissions, and user_roles tables with system roles seed.

Revision ID: 0042
Revises: 0041
"""
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM as PG_ENUM

revision = "0042"
down_revision = "0041"
branch_labels = None
depends_on = None

SYSTEM_PERMISSIONS = [
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

SYSTEM_ROLES = [
    (
        "superadministrador",
        "Superadministrador",
        "superadministrador",
        [p[0] for p in SYSTEM_PERMISSIONS],
    ),
    (
        "administrador",
        "Administrador",
        "administrador",
        [p[0] for p in SYSTEM_PERMISSIONS],
    ),
    (
        "encargado",
        "Encargado de Sucursal",
        "encargado",
        [
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
    ),
    (
        "cajero",
        "Cajero",
        "cajero",
        [
            "sales:create",
            "sales:read",
            "inventory:read",
            "reservations:manage",
            "orders:manage",
        ],
    ),
    (
        "proveedor",
        "Proveedor",
        "proveedor",
        ["replenishment:manage", "catalog:manage"],
    ),
    (
        "cliente",
        "Cliente",
        "cliente",
        ["reservations:manage", "orders:manage"],
    ),
    (
        "delivery",
        "Repartidor / Delivery",
        "delivery",
        ["orders:manage"],
    ),
]


def upgrade() -> None:
    op.create_table(
        "permissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("module", sa.String(50), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_permissions_name", "permissions", ["name"])
    op.create_index("ix_permissions_module", "permissions", ["module"])

    op.create_table(
        "roles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column(
            "base_rol",
            PG_ENUM("cliente", "administrador", "encargado", "cajero", "proveedor", "delivery", "superadministrador", name="rolenum", create_type=False),
            nullable=True,
        ),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_roles_tenant_code"),
    )
    op.create_index("ix_roles_tenant_id", "roles", ["tenant_id"])

    op.create_table(
        "role_permissions",
        sa.Column("role_id", UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", UUID(as_uuid=True), sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "user_roles",
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    )

    # Seed permissions
    perm_table = sa.table(
        "permissions",
        sa.column("id", UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("module", sa.String),
        sa.column("description", sa.String),
    )
    perm_id_map = {}
    for name, module, desc in SYSTEM_PERMISSIONS:
        pid = uuid.uuid5(uuid.NAMESPACE_DNS, f"rbac.permission.{name}")
        perm_id_map[name] = pid
        op.execute(
            perm_table.insert().values(
                id=pid,
                name=name,
                module=module,
                description=desc,
            )
        )

    # Seed system roles
    role_table = sa.table(
        "roles",
        sa.column("id", UUID(as_uuid=True)),
        sa.column("tenant_id", UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("base_rol", sa.String),
        sa.column("is_system", sa.Boolean),
    )
    role_perm_table = sa.table(
        "role_permissions",
        sa.column("role_id", UUID(as_uuid=True)),
        sa.column("permission_id", UUID(as_uuid=True)),
    )

    for code, name, base_rol, perms in SYSTEM_ROLES:
        rid = uuid.uuid5(uuid.NAMESPACE_DNS, f"rbac.role.{code}")
        op.execute(
            role_table.insert().values(
                id=rid,
                tenant_id=None,
                code=code,
                name=name,
                base_rol=base_rol,
                is_system=True,
            )
        )
        for p in perms:
            if p in perm_id_map:
                op.execute(
                    role_perm_table.insert().values(
                        role_id=rid,
                        permission_id=perm_id_map[p],
                    )
                )


def downgrade() -> None:
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_index("ix_roles_tenant_id", "roles")
    op.drop_table("roles")
    op.drop_index("ix_permissions_module", "permissions")
    op.drop_index("ix_permissions_name", "permissions")
    op.drop_table("permissions")
