"""CU30: offline queue by time. Store when each offline sale/order happened so the earliest keeps the stock.

Revision ID: 0056
Revises: 0055
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0056"
down_revision = "0055"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sales", sa.Column("offline_created_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("sales", sa.Column("offline_details", JSONB, nullable=True))
    op.create_index("ix_sales_offline_created_at", "sales", ["offline_created_at"])
    op.add_column("orders", sa.Column("offline_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_orders_offline_requested_at", "orders", ["offline_requested_at"])


def downgrade() -> None:
    op.drop_index("ix_orders_offline_requested_at", "orders")
    op.drop_column("orders", "offline_requested_at")
    op.drop_index("ix_sales_offline_created_at", "sales")
    op.drop_column("sales", "offline_details")
    op.drop_column("sales", "offline_created_at")
