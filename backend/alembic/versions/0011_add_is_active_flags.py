"""add is_active flags to users branches and providers

Revision ID: 0011_add_is_active_flags
Revises: 0010_cleanup_catalog
Create Date: 2026-09-04 00:00:03.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


revision = "0011_add_is_active_flags"
down_revision = "0010_cleanup_catalog"
branch_labels = None
depends_on = None


def _add_boolean_column(table_name: str, column_name: str) -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns(table_name)} if inspector.has_table(table_name) else set()
    if column_name in columns:
        return

    op.add_column(
        table_name,
        sa.Column(column_name, sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def upgrade() -> None:
    _add_boolean_column("users", "is_active")
    _add_boolean_column("branches", "is_active")
    _add_boolean_column("providers", "is_active")

    bind = op.get_bind()
    inspector = inspect(bind)
    if inspector.has_table("providers"):
        op.execute(text("UPDATE providers SET is_active = CASE WHEN status = 'active' THEN TRUE ELSE FALSE END"))


def _drop_boolean_column(table_name: str, column_name: str) -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns(table_name)} if inspector.has_table(table_name) else set()
    if column_name not in columns:
        return

    with op.batch_alter_table(table_name) as batch_op:
        batch_op.drop_column(column_name)


def downgrade() -> None:
    _drop_boolean_column("providers", "is_active")
    _drop_boolean_column("branches", "is_active")
    _drop_boolean_column("users", "is_active")
