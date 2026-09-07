"""add carts

Revision ID: 0015_add_carts
Revises: 0014_add_inventory_movements
Create Date: 2026-09-07 01:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID


revision = "0015_add_carts"
down_revision = "0014_add_inventory_movements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    cart_status_enum = sa.Enum("active", "checked_out", "cancelled", name="cartstatusenum")
    if not inspector.has_table("carts"):
        cart_status_enum.create(bind, checkfirst=True)
        op.create_table(
            "carts",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", UUID(as_uuid=True), nullable=False),
            sa.Column("status", cart_status_enum, nullable=False),
            sa.Column("subtotal", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("discount_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("total_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.UniqueConstraint("user_id", name="uq_carts_user_id"),
        )

    if not inspector.has_table("cart_items"):
        op.create_table(
            "cart_items",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("cart_id", UUID(as_uuid=True), nullable=False),
            sa.Column("variant_id", UUID(as_uuid=True), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
            sa.ForeignKeyConstraint(["cart_id"], ["carts.id"]),
            sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"]),
            sa.UniqueConstraint("cart_id", "variant_id", name="uq_cart_item_cart_variant"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("cart_items"):
        op.drop_table("cart_items")
    if inspector.has_table("carts"):
        op.drop_table("carts")

    cart_status_enum = sa.Enum("active", "checked_out", "cancelled", name="cartstatusenum")
    cart_status_enum.drop(bind, checkfirst=True)
