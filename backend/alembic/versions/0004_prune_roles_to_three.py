"""prune roles to three values

Revision ID: 0004_prune_roles_to_three
Revises: 0003_spanish_enum_values
Create Date: 2026-08-25 00:00:03.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0004_prune_roles_to_three"
down_revision = "0003_spanish_enum_values"
branch_labels = None
depends_on = None


DESIRED_VALUES = {"administrador", "cliente", "delivery"}


def _current_enum_values(inspector, type_name: str) -> set[str]:
    enums = {enum["name"]: set(enum["labels"]) for enum in inspector.get_enums()}
    return enums.get(type_name, set())


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("users"):
        return

    current_values = _current_enum_values(inspector, "rolenum")
    if current_values == DESIRED_VALUES:
        return

    op.execute(sa.text("CREATE TYPE rolenum_new AS ENUM ('administrador', 'cliente', 'delivery')"))
    op.execute(
        sa.text(
            """
            ALTER TABLE users
            ALTER COLUMN rol TYPE rolenum_new
            USING (
                CASE
                    WHEN rol::text IN ('administrador', 'admin') THEN 'administrador'
                    WHEN rol::text IN ('cliente', 'customer') THEN 'cliente'
                    ELSE 'delivery'
                END
            )::rolenum_new
            """
        )
    )
    op.execute(sa.text("DROP TYPE rolenum"))
    op.execute(sa.text("ALTER TYPE rolenum_new RENAME TO rolenum"))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("users"):
        return

    current_values = _current_enum_values(inspector, "rolenum")
    if current_values != DESIRED_VALUES:
        return

    op.execute(
        sa.text(
            """
            CREATE TYPE rolenum_old AS ENUM (
                'administrador',
                'catalogo',
                'inventario',
                'pedidos',
                'soporte_cliente',
                'cliente'
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            ALTER TABLE users
            ALTER COLUMN rol TYPE rolenum_old
            USING (
                CASE
                    WHEN rol::text = 'administrador' THEN 'administrador'
                    WHEN rol::text = 'cliente' THEN 'cliente'
                    ELSE 'soporte_cliente'
                END
            )::rolenum_old
            """
        )
    )
    op.execute(sa.text("DROP TYPE rolenum"))
    op.execute(sa.text("ALTER TYPE rolenum_old RENAME TO rolenum"))
