"""CU25/CU30: persist offline sale conflicts and make offline sales idempotent.

Revision ID: 0055
Revises: 0054
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0055"
down_revision = "0054"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sales", sa.Column("offline_operation_id", sa.String(64), nullable=True))
    op.create_unique_constraint("sales_offline_operation_id_key", "sales", ["offline_operation_id"])

    op.create_table(
        "offline_sale_conflicts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("branch_id", UUID(as_uuid=True), sa.ForeignKey("branches.id"), nullable=False, index=True),
        sa.Column("cashier_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("cash_session_id", UUID(as_uuid=True), sa.ForeignKey("cash_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("operation_id", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("receipt_number", sa.String(40), nullable=False),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("items", JSONB, nullable=False),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("discount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("cash_received", sa.Numeric(10, 2), nullable=True),
        sa.Column("change_returned", sa.Numeric(10, 2), nullable=True),
        sa.Column("customer_name", sa.String(120), nullable=True),
        sa.Column("customer_phone", sa.String(40), nullable=True),
        sa.Column("customer_email", sa.String(255), nullable=True),
        sa.Column("offline_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(12), nullable=False, server_default="pending", index=True),
        sa.Column("resolution", sa.String(20), nullable=True),
        sa.Column("refund_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("wallet_credit_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("extra_charged", sa.Numeric(10, 2), nullable=True),
        sa.Column("sale_id", UUID(as_uuid=True), sa.ForeignKey("sales.id", ondelete="SET NULL"), nullable=True),
        sa.Column("refund_receipt_number", sa.String(48), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("resolved_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("offline_sale_conflicts")
    op.drop_constraint("sales_offline_operation_id_key", "sales", type_="unique")
    op.drop_column("sales", "offline_operation_id")
