"""make providers global

Revision ID: 0030
Revises: 0029
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID


revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("providers"):
        return

    columns = {column["name"] for column in inspector.get_columns("providers")}
    if "branch_id" not in columns:
        return

    for constraint in inspector.get_foreign_keys("providers"):
        if "branch_id" in constraint.get("constrained_columns", []):
            op.drop_constraint(constraint["name"], "providers", type_="foreignkey")
    op.drop_column("providers", "branch_id")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("providers"):
        return

    columns = {column["name"] for column in inspector.get_columns("providers")}
    if "branch_id" in columns:
        return

    op.add_column("providers", sa.Column("branch_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_providers_branch_id_branches", "providers", "branches", ["branch_id"], ["id"])
    indexes = {index["name"] for index in inspector.get_indexes("providers")}
    if "ix_providers_branch_id" not in indexes:
        op.create_index("ix_providers_branch_id", "providers", ["branch_id"])
