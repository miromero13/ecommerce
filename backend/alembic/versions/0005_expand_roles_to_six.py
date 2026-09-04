"""expand roles to six values

Revision ID: 0005_expand_roles_to_six
Revises: 0004_prune_roles_to_three
Create Date: 2026-09-04 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0005_expand_roles_to_six"
down_revision = "0004_prune_roles_to_three"
branch_labels = None
depends_on = None


DESIRED_VALUES = {
    "administrador",
    "cliente",
    "proveedor",
    "encargado",
    "cajero",
    "delivery",
}


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

    op.execute(
        sa.text(
            "CREATE TYPE rolenum_new AS ENUM ('administrador', 'cliente', 'proveedor', 'encargado', 'cajero', 'delivery')"
        )
    )
    op.execute(
        sa.text(
            """
            ALTER TABLE users
            ALTER COLUMN rol TYPE rolenum_new
            USING (
                CASE
                    WHEN rol::text IN ('administrador', 'admin') THEN 'administrador'
                    WHEN rol::text IN ('cliente', 'customer') THEN 'cliente'
                    WHEN rol::text = 'proveedor' THEN 'proveedor'
                    WHEN rol::text = 'encargado' THEN 'encargado'
                    WHEN rol::text = 'cajero' THEN 'cajero'
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
        sa.text("CREATE TYPE rolenum_old AS ENUM ('administrador', 'cliente', 'delivery')")
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
                    ELSE 'delivery'
                END
            )::rolenum_old
            """
        )
    )
    op.execute(sa.text("DROP TYPE rolenum"))
    op.execute(sa.text("ALTER TYPE rolenum_old RENAME TO rolenum"))
