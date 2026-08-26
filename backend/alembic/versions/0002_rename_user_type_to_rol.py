"""rename user_type to rol

Revision ID: 0002_rename_user_type_to_rol
Revises: 0001_initial_users
Create Date: 2026-08-25 00:00:00.000001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0002_rename_user_type_to_rol"
down_revision = "0001_initial_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("users"):
        return

    columns = {column["name"] for column in inspector.get_columns("users")}

    if "user_type" in columns and "rol" not in columns:
        op.alter_column("users", "user_type", new_column_name="rol")

        # Renombra el tipo enum viejo para que coincida con el modelo nuevo.
        op.execute(sa.text("ALTER TYPE usertypeenum RENAME TO rolenum"))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("users"):
        return

    columns = {column["name"] for column in inspector.get_columns("users")}

    if "rol" in columns and "user_type" not in columns:
        op.execute(sa.text("ALTER TYPE rolenum RENAME TO usertypeenum"))
        op.alter_column("users", "rol", new_column_name="user_type")
