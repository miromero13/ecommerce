"""add promotion codes

Revision ID: 0022
 Revises: 0021
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "promotion_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("discount_type", sa.String(length=20), nullable=False),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("branch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("branches.id"), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("code", name="uq_promotion_codes_code"),
    )
    op.create_index("ix_promotion_codes_code", "promotion_codes", ["code"])
    op.create_index("ix_promotion_codes_branch_id", "promotion_codes", ["branch_id"])
    op.create_index("ix_promotion_codes_created_by", "promotion_codes", ["created_by"])
    op.create_table(
        "promotion_code_usages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("promotion_code_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("promotion_codes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("promotion_code_id", "user_id", name="uq_promotion_code_usage_user"),
    )
    op.create_index("ix_promotion_code_usages_promotion_code_id", "promotion_code_usages", ["promotion_code_id"])
    op.create_index("ix_promotion_code_usages_user_id", "promotion_code_usages", ["user_id"])

    op.add_column("carts", sa.Column("promotion_code_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("promotion_codes.id"), nullable=True))
    op.add_column("orders", sa.Column("promotion_code_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("promotion_codes.id"), nullable=True))


def downgrade() -> None:
    op.drop_column("orders", "promotion_code_id")
    op.drop_column("carts", "promotion_code_id")
    op.drop_table("promotion_code_usages")
    op.drop_index("ix_promotion_codes_created_by", table_name="promotion_codes")
    op.drop_index("ix_promotion_codes_branch_id", table_name="promotion_codes")
    op.drop_index("ix_promotion_codes_code", table_name="promotion_codes")
    op.drop_table("promotion_codes")
