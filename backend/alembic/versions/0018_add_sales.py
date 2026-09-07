"""add sales

Revision ID: 0018_add_sales
Revises: 0017_add_orders
Create Date: 2026-09-07 04:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID, ENUM as PG_ENUM


revision = "0018_add_sales"
down_revision = "0017_add_orders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    sale_status_enum = PG_ENUM("completed", "cancelled", name="salestatusenum", create_type=False)
    payment_method_enum = PG_ENUM("cash", "stripe", name="paymentmethodenum", create_type=False)
    payment_status_enum = PG_ENUM("pending", "paid", "failed", name="paymentstatusenum", create_type=False)

    if not inspector.has_table("sales"):
        sale_status_enum.create(bind, checkfirst=True)
        op.create_table(
            "sales",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("branch_id", UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", UUID(as_uuid=True), nullable=False),
            sa.Column("reservation_id", UUID(as_uuid=True), nullable=True),
            sa.Column("status", sale_status_enum, nullable=False),
            sa.Column("payment_method", payment_method_enum, nullable=False),
            sa.Column("payment_status", payment_status_enum, nullable=False),
            sa.Column("cash_reference", sa.String(), nullable=True),
            sa.Column("subtotal", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("discount_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("total_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(), nullable=False, server_default="usd"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["reservation_id"], ["reservations.id"]),
            sa.UniqueConstraint("reservation_id", name="uq_sales_reservation_id"),
        )

    if not inspector.has_table("sale_items"):
        op.create_table(
            "sale_items",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("sale_id", UUID(as_uuid=True), nullable=False),
            sa.Column("variant_id", UUID(as_uuid=True), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
            sa.Column("line_total", sa.Numeric(10, 2), nullable=False),
            sa.Column("product_id", UUID(as_uuid=True), nullable=False),
            sa.Column("product_name", sa.String(), nullable=False),
            sa.Column("variant_sku", sa.String(), nullable=False),
            sa.Column("size_id", UUID(as_uuid=True), nullable=True),
            sa.Column("color_id", UUID(as_uuid=True), nullable=True),
            sa.Column("image_url", sa.String(), nullable=True),
            sa.Column("image_public_id", sa.String(), nullable=True),
            sa.ForeignKeyConstraint(["sale_id"], ["sales.id"]),
            sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"]),
            sa.UniqueConstraint("sale_id", "variant_id", name="uq_sale_item_sale_variant"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("sale_items"):
        op.drop_table("sale_items")
    if inspector.has_table("sales"):
        op.drop_table("sales")

    op.execute("DROP TYPE IF EXISTS salestatusenum")
