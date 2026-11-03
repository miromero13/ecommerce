"""CU18 & CU19: add gift cards and store wallet tables, plus wallet payment method.

Revision ID: 0053
Revises: 0052
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0053"
down_revision = "0052"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'wallet' to paymentmethodenum if not exists
    op.execute("ALTER TYPE paymentmethodenum ADD VALUE IF NOT EXISTS 'wallet'")

    op.create_table(
        "gift_cards",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("buyer_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("code", sa.String(32), nullable=False, unique=True, index=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("balance", sa.Numeric(10, 2), nullable=False),
        sa.Column("recipient_name", sa.String(120), nullable=False),
        sa.Column("recipient_email", sa.String(255), nullable=False, index=True),
        sa.Column("custom_message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("payment_method", sa.String(30), nullable=False, server_default="stripe"),
        sa.Column("stripe_payment_intent_id", sa.String(120), nullable=True),
        sa.Column("qr_code_url", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("redeemed_by_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("amount >= 10.00", name="ck_gift_card_min_amount"),
        sa.CheckConstraint("balance >= 0", name="ck_gift_card_balance_non_negative"),
    )

    op.create_table(
        "user_wallets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, unique=True),
        sa.Column("balance", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="BOB"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("balance >= 0", name="ck_wallet_balance_non_negative"),
    )

    op.create_table(
        "wallet_transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("wallet_id", UUID(as_uuid=True), sa.ForeignKey("user_wallets.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("type", sa.String(10), nullable=False),  # credit | debit
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("balance_after", sa.Numeric(10, 2), nullable=False),
        sa.Column("concept", sa.String(30), nullable=False),  # gift_card_redeem | order_payment | sale_payment | rma_refund
        sa.Column("source_type", sa.String(30), nullable=True),
        sa.Column("source_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("amount > 0", name="ck_wallet_tx_amount_positive"),
    )


def downgrade() -> None:
    op.drop_table("wallet_transactions")
    op.drop_table("user_wallets")
    op.drop_table("gift_cards")
