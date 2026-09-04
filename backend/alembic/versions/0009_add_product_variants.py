"""add product variants

Revision ID: 0009_add_product_variants
Revises: 0008_catalog_inventory
Create Date: 2026-09-04 01:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID, ENUM as PG_ENUM
import uuid


revision = "0009_add_product_variants"
down_revision = "0008_catalog_inventory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("product_variants"):
        product_status_enum = PG_ENUM(
            "pending",
            "active",
            "inactive",
            name="productstatusenum",
            create_type=False,
        )
        op.create_table(
            "product_variants",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("product_id", UUID(as_uuid=True), nullable=False),
            sa.Column("sku", sa.String(), nullable=False, unique=True),
            sa.Column("price", sa.Numeric(10, 2), nullable=False),
            sa.Column("size_id", UUID(as_uuid=True), nullable=True),
            sa.Column("color_id", UUID(as_uuid=True), nullable=True),
            sa.Column("status", product_status_enum, nullable=False),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.ForeignKeyConstraint(["size_id"], ["sizes.id"]),
            sa.ForeignKeyConstraint(["color_id"], ["colors.id"]),
            sa.UniqueConstraint("product_id", "size_id", "color_id", name="uq_product_variant_combo"),
        )

    if inspector.has_table("inventory"):
        columns = {column["name"] for column in inspector.get_columns("inventory")}
        if "variant_id" not in columns:
            op.add_column("inventory", sa.Column("variant_id", UUID(as_uuid=True), nullable=True))

        try:
            op.drop_constraint("uq_inventory_product_branch", "inventory", type_="unique")
        except Exception:
            pass

        op.create_unique_constraint("uq_inventory_variant_branch", "inventory", ["variant_id", "branch_id"])

        products = bind.execute(sa.text("SELECT id, sku, price, size_id, color_id, status FROM products ORDER BY name ASC")).fetchall()
        variant_rows = []
        for product in products:
            variant_rows.append(
                {
                    "id": uuid.uuid4(),
                    "product_id": product.id,
                    "sku": product.sku,
                    "price": product.price,
                    "size_id": product.size_id,
                    "color_id": product.color_id,
                    "status": product.status,
                }
            )

        if variant_rows:
            product_variants = sa.table(
                "product_variants",
                sa.column("id", UUID(as_uuid=True)),
                sa.column("product_id", UUID(as_uuid=True)),
                sa.column("sku", sa.String()),
                sa.column("price", sa.Numeric(10, 2)),
                sa.column("size_id", UUID(as_uuid=True)),
                sa.column("color_id", UUID(as_uuid=True)),
                sa.column("status", sa.String()),
            )
            op.bulk_insert(product_variants, variant_rows)

            bind.execute(
                sa.text(
                    """
                    UPDATE inventory i
                    SET variant_id = pv.id
                    FROM product_variants pv
                    WHERE i.product_id = pv.product_id
                      AND i.variant_id IS NULL
                    """
                )
            )

        op.alter_column("inventory", "variant_id", nullable=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("inventory"):
        try:
            op.drop_constraint("uq_inventory_variant_branch", "inventory", type_="unique")
        except Exception:
            pass
        if "variant_id" in {column["name"] for column in inspector.get_columns("inventory")}:
            op.drop_column("inventory", "variant_id")
        op.create_unique_constraint("uq_inventory_product_branch", "inventory", ["product_id", "branch_id"])

    if inspector.has_table("product_variants"):
        op.drop_table("product_variants")
