"""Add branch_id to carts table for branch-level validation and scoping.

Revision ID: 0052
Revises: 0051
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0052"
down_revision = "0051"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("carts", sa.Column("branch_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_carts_branch_id_branches",
        "carts",
        "branches",
        ["branch_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_carts_branch_id", "carts", ["branch_id"])


def downgrade() -> None:
    op.drop_index("ix_carts_branch_id", table_name="carts")
    op.drop_constraint("fk_carts_branch_id_branches", "carts", type_="foreignkey")
    op.drop_column("carts", "branch_id")
