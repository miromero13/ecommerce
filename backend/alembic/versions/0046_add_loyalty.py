"""CU17: loyalty accounts, points ledger and the points discount of web orders.

Revision ID: 0046
Revises: 0045
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0046"
down_revision = "0045"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "loyalty_accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("points_balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lifetime_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_loyalty_account_tenant_user"),
        sa.CheckConstraint("points_balance >= 0", name="ck_loyalty_balance_non_negative"),
    )
    op.create_table(
        "loyalty_ledger",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("loyalty_accounts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(10), nullable=False),
        sa.Column("source_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("source_type", "source_id", "type", name="uq_loyalty_ledger_source_type"),
        sa.CheckConstraint("points > 0", name="ck_loyalty_ledger_points_positive"),
    )
    op.add_column("orders", sa.Column("loyalty_discount", sa.Numeric(10, 2), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("orders", "loyalty_discount")
    op.drop_table("loyalty_ledger")
    op.drop_table("loyalty_accounts")
