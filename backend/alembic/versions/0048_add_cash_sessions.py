"""1P-CU18: cash drawer sessions (opening, movements with change given, closing count).

Revision ID: 0048
Revises: 0047
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0048"
down_revision = "0047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cash_sessions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("branch_id", UUID(as_uuid=True), sa.ForeignKey("branches.id"), nullable=False, index=True),
        sa.Column("cashier_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("status", sa.String(10), nullable=False, server_default="open"),
        sa.Column("opening_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expected_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("counted_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("difference", sa.Numeric(10, 2), nullable=True),
        sa.Column("closing_note", sa.String(255), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('open', 'closed')", name="ck_cash_sessions_status"),
        sa.CheckConstraint("opening_amount >= 0", name="ck_cash_sessions_opening_non_negative"),
    )
    op.create_index("uq_cash_sessions_open_cashier", "cash_sessions", ["cashier_id"], unique=True,
                    postgresql_where=sa.text("status = 'open'"))
    op.create_table(
        "cash_movements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", UUID(as_uuid=True), sa.ForeignKey("cash_sessions.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("type", sa.String(12), nullable=False),
        sa.Column("method", sa.String(6), nullable=False, server_default="cash"),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("cash_received", sa.Numeric(10, 2), nullable=True),
        sa.Column("change_given", sa.Numeric(10, 2), nullable=True),
        sa.Column("source_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("type IN ('sale', 'deposit', 'withdrawal')", name="ck_cash_movements_type"),
        sa.CheckConstraint("method IN ('cash', 'qr')", name="ck_cash_movements_method"),
        sa.CheckConstraint("amount >= 0", name="ck_cash_movements_amount_non_negative"),  # a sale paid fully with points is 0
        sa.CheckConstraint("change_given IS NULL OR change_given >= 0", name="ck_cash_movements_change_non_negative"),
    )


def downgrade() -> None:
    op.drop_table("cash_movements")
    op.drop_index("uq_cash_sessions_open_cashier", table_name="cash_sessions")
    op.drop_table("cash_sessions")
