"""Simple payment receipts (comprobantes) for every payment transaction.

Revision ID: 0049
Revises: 0048
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0049"
down_revision = "0048"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_receipts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("issuer", sa.String(10), nullable=False),
        sa.Column("series", sa.String(40), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("source_id", UUID(as_uuid=True), nullable=False),
        sa.Column("branch_id", UUID(as_uuid=True), sa.ForeignKey("branches.id"), nullable=True, index=True),
        sa.Column("customer_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("customer_name", sa.String(150), nullable=True),
        sa.Column("customer_email", sa.String(255), nullable=True),
        sa.Column("payment_method", sa.String(10), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("lines", JSONB(), nullable=False),
        sa.Column("summary", JSONB(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("emailed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("email_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("series", "number", name="uq_payment_receipts_series_number"),
        sa.UniqueConstraint("kind", "source_id", name="uq_payment_receipts_source"),
        sa.CheckConstraint("issuer IN ('company', 'platform')", name="ck_payment_receipts_issuer"),
        sa.CheckConstraint("kind IN ('order', 'sale', 'reservation_deposit', 'subscription')", name="ck_payment_receipts_kind"),
        sa.CheckConstraint("payment_method IN ('card', 'qr', 'cash')", name="ck_payment_receipts_method"),
    )


def downgrade() -> None:
    op.drop_table("payment_receipts")
