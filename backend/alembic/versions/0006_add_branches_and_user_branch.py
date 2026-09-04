"""add branches and user branch

Revision ID: 0006_add_branches_and_user_branch
Revises: 0005_expand_roles_to_six
Create Date: 2026-09-04 00:00:01.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID


revision = "0006_add_branches_and_user_branch"
down_revision = "0005_expand_roles_to_six"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("branches"):
        op.create_table(
            "branches",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.String(), nullable=False, unique=True),
            sa.Column("city", sa.String(), nullable=False),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.PrimaryKeyConstraint("id"),
        )

    columns = {column["name"] for column in inspector.get_columns("users")} if inspector.has_table("users") else set()
    if "branch_id" not in columns and inspector.has_table("users"):
        op.add_column(
            "users",
            sa.Column("branch_id", UUID(as_uuid=True), nullable=True),
        )

    if inspector.has_table("users"):
        op.create_foreign_key(
            "fk_users_branch_id_branches",
            "users",
            "branches",
            ["branch_id"],
            ["id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("users"):
        op.drop_constraint("fk_users_branch_id_branches", "users", type_="foreignkey")
        with op.batch_alter_table("users") as batch_op:
            batch_op.drop_column("branch_id")

    if inspector.has_table("branches"):
        op.drop_table("branches")
