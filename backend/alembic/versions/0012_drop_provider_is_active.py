"""drop providers is_active

Revision ID: 0012_drop_provider_is_active
Revises: 0011_add_is_active_flags
Create Date: 2026-09-04 00:00:04.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0012_drop_provider_is_active"
down_revision = "0011_add_is_active_flags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("providers")} if inspector.has_table("providers") else set()
    if "is_active" in columns:
        with op.batch_alter_table("providers") as batch_op:
            batch_op.drop_column("is_active")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("providers")} if inspector.has_table("providers") else set()
    if "is_active" not in columns:
        op.add_column(
            "providers",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
        op.execute("UPDATE providers SET is_active = CASE WHEN status = 'active' THEN TRUE ELSE FALSE END")