"""translate enum values to spanish

Revision ID: 0003_spanish_enum_values
Revises: 0002_rename_user_type_to_rol
Create Date: 2026-08-25 00:00:02.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0003_spanish_enum_values"
down_revision = "0002_rename_user_type_to_rol"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("users"):
        return

    enums = {enum["name"]: set(enum["labels"]) for enum in inspector.get_enums()}

    if "genderenum" in enums and "male" in enums["genderenum"]:
        op.execute(sa.text("ALTER TYPE genderenum RENAME VALUE 'male' TO 'masculino'"))
    if "genderenum" in enums and "female" in enums["genderenum"]:
        op.execute(sa.text("ALTER TYPE genderenum RENAME VALUE 'female' TO 'femenino'"))

    if "rolenum" in enums and "admin" in enums["rolenum"]:
        op.execute(sa.text("ALTER TYPE rolenum RENAME VALUE 'admin' TO 'administrador'"))
    if "rolenum" in enums and "catalog_manager" in enums["rolenum"]:
        op.execute(sa.text("ALTER TYPE rolenum RENAME VALUE 'catalog_manager' TO 'catalogo'"))
    if "rolenum" in enums and "inventory_manager" in enums["rolenum"]:
        op.execute(sa.text("ALTER TYPE rolenum RENAME VALUE 'inventory_manager' TO 'inventario'"))
    if "rolenum" in enums and "order_manager" in enums["rolenum"]:
        op.execute(sa.text("ALTER TYPE rolenum RENAME VALUE 'order_manager' TO 'pedidos'"))
    if "rolenum" in enums and "customer_support" in enums["rolenum"]:
        op.execute(sa.text("ALTER TYPE rolenum RENAME VALUE 'customer_support' TO 'soporte_cliente'"))
    if "rolenum" in enums and "customer" in enums["rolenum"]:
        op.execute(sa.text("ALTER TYPE rolenum RENAME VALUE 'customer' TO 'cliente'"))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("users"):
        return

    enums = {enum["name"]: set(enum["labels"]) for enum in inspector.get_enums()}

    if "genderenum" in enums and "masculino" in enums["genderenum"]:
        op.execute(sa.text("ALTER TYPE genderenum RENAME VALUE 'masculino' TO 'male'"))
    if "genderenum" in enums and "femenino" in enums["genderenum"]:
        op.execute(sa.text("ALTER TYPE genderenum RENAME VALUE 'femenino' TO 'female'"))

    if "rolenum" in enums and "administrador" in enums["rolenum"]:
        op.execute(sa.text("ALTER TYPE rolenum RENAME VALUE 'administrador' TO 'admin'"))
    if "rolenum" in enums and "catalogo" in enums["rolenum"]:
        op.execute(sa.text("ALTER TYPE rolenum RENAME VALUE 'catalogo' TO 'catalog_manager'"))
    if "rolenum" in enums and "inventario" in enums["rolenum"]:
        op.execute(sa.text("ALTER TYPE rolenum RENAME VALUE 'inventario' TO 'inventory_manager'"))
    if "rolenum" in enums and "pedidos" in enums["rolenum"]:
        op.execute(sa.text("ALTER TYPE rolenum RENAME VALUE 'pedidos' TO 'order_manager'"))
    if "rolenum" in enums and "soporte_cliente" in enums["rolenum"]:
        op.execute(sa.text("ALTER TYPE rolenum RENAME VALUE 'soporte_cliente' TO 'customer_support'"))
    if "rolenum" in enums and "cliente" in enums["rolenum"]:
        op.execute(sa.text("ALTER TYPE rolenum RENAME VALUE 'cliente' TO 'customer'"))
