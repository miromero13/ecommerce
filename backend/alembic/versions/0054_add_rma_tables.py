"""CU21 & CU24: add rma_requests and rma_request_items tables and expand inventorymovementtypeenum.

Revision ID: 0054
Revises: 0053
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0054"
down_revision = "0053"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new movement types to inventorymovementtypeenum if postgres enum exists
    for val in ("rma_restock", "exchange_dispatch", "scrap_quarantine"):
        op.execute(f"ALTER TYPE inventorymovementtypeenum ADD VALUE IF NOT EXISTS '{val}'")

    op.create_table(
        "rma_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("order_id", UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("rma_number", sa.String(32), nullable=False, unique=True, index=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending_inspection"),
        sa.Column("customer_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "rma_request_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("rma_id", UUID(as_uuid=True), sa.ForeignKey("rma_requests.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("order_item_id", UUID(as_uuid=True), sa.ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("reason", sa.String(30), nullable=False),
        sa.Column("preferred_resolution", sa.String(30), nullable=False),
        sa.Column("requested_variant_id", UUID(as_uuid=True), sa.ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("customer_notes", sa.Text(), nullable=True),
        sa.Column("item_condition", sa.String(30), nullable=True),
        sa.Column("action", sa.String(30), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("replacement_variant_id", UUID(as_uuid=True), sa.ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("branch_id", UUID(as_uuid=True), sa.ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("inspection_notes", sa.Text(), nullable=True),
        sa.Column("quarantine_record", sa.String(64), nullable=True, index=True),
        sa.Column("restock_movement_id", UUID(as_uuid=True), sa.ForeignKey("inventory_movements.id", ondelete="SET NULL"), nullable=True),
        sa.Column("dispatch_movement_id", UUID(as_uuid=True), sa.ForeignKey("inventory_movements.id", ondelete="SET NULL"), nullable=True),
        sa.Column("refund_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("wallet_settlement_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("settlement_status", sa.String(30), nullable=True),
        sa.Column("inspected_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("inspected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("rma_request_items")
    op.drop_table("rma_requests")
