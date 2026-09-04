"""add catalog and inventory base

Revision ID: 0008_add_catalog_and_inventory_base
Revises: 0007_add_providers
Create Date: 2026-09-04 00:00:03.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID


revision = "0008_add_catalog_and_inventory_base"
down_revision = "0007_add_providers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("categories"):
        op.create_table(
            "categories",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.String(), nullable=False, unique=True),
        )

    if not inspector.has_table("sizes"):
        op.create_table(
            "sizes",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.String(), nullable=False, unique=True),
        )

    if not inspector.has_table("colors"):
        op.create_table(
            "colors",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.String(), nullable=False, unique=True),
            sa.Column("hex_code", sa.String(), nullable=True),
        )

    if not inspector.has_table("seasons"):
        op.create_table(
            "seasons",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.String(), nullable=False, unique=True),
        )

    if not inspector.has_table("collections"):
        op.create_table(
            "collections",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.String(), nullable=False, unique=True),
            sa.Column("season_id", UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(["season_id"], ["seasons.id"]),
        )

    if not inspector.has_table("products"):
        op.create_table(
            "products",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("sku", sa.String(), nullable=False, unique=True),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("price", sa.Numeric(10, 2), nullable=False),
            sa.Column("status", sa.Enum("pending", "active", "inactive", name="productstatusenum"), nullable=False),
            sa.Column("provider_id", UUID(as_uuid=True), nullable=True),
            sa.Column("category_id", UUID(as_uuid=True), nullable=False),
            sa.Column("size_id", UUID(as_uuid=True), nullable=True),
            sa.Column("color_id", UUID(as_uuid=True), nullable=True),
            sa.Column("season_id", UUID(as_uuid=True), nullable=True),
            sa.Column("collection_id", UUID(as_uuid=True), nullable=True),
            sa.ForeignKeyConstraint(["provider_id"], ["providers.id"]),
            sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
            sa.ForeignKeyConstraint(["size_id"], ["sizes.id"]),
            sa.ForeignKeyConstraint(["color_id"], ["colors.id"]),
            sa.ForeignKeyConstraint(["season_id"], ["seasons.id"]),
            sa.ForeignKeyConstraint(["collection_id"], ["collections.id"]),
        )

    if not inspector.has_table("inventory"):
        op.create_table(
            "inventory",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("product_id", UUID(as_uuid=True), nullable=False),
            sa.Column("branch_id", UUID(as_uuid=True), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("reserved_quantity", sa.Integer(), nullable=False, server_default="0"),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
            sa.UniqueConstraint("product_id", "branch_id", name="uq_inventory_product_branch"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("inventory"):
        op.drop_table("inventory")
    if inspector.has_table("products"):
        op.drop_table("products")
    if inspector.has_table("collections"):
        op.drop_table("collections")
    if inspector.has_table("seasons"):
        op.drop_table("seasons")
    if inspector.has_table("colors"):
        op.drop_table("colors")
    if inspector.has_table("sizes"):
        op.drop_table("sizes")
    if inspector.has_table("categories"):
        op.drop_table("categories")
