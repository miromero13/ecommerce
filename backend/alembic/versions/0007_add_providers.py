"""add providers

Revision ID: 0007_add_providers
Revises: 0006_add_branches_and_user_branch
Create Date: 2026-09-04 00:00:02.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID


revision = "0007_add_providers"
down_revision = "0006_add_branches_and_user_branch"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("providers"):
        op.create_table(
            "providers",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", UUID(as_uuid=True), nullable=False),
            sa.Column("branch_id", UUID(as_uuid=True), nullable=True),
            sa.Column("business_name", sa.String(), nullable=False),
            sa.Column("contact_name", sa.String(), nullable=False),
            sa.Column("phone", sa.String(), nullable=True),
            sa.Column("status", sa.Enum("active", "suspended", name="providerstatusenum"), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
            sa.UniqueConstraint("user_id"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("providers"):
        op.drop_table("providers")
