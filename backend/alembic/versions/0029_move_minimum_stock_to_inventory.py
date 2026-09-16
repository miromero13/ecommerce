"""move minimum stock from products to inventory

Revision ID: 0029
Revises: 0028
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    inventory_columns = {column["name"] for column in inspector.get_columns("inventory")}
    if "minimum_stock" not in inventory_columns:
        op.add_column("inventory", sa.Column("minimum_stock", sa.Integer(), nullable=False, server_default="0"))
        op.create_check_constraint("ck_inventory_minimum_stock_non_negative", "inventory", "minimum_stock >= 0")

    product_columns = {column["name"] for column in inspector.get_columns("products")}
    if "minimum_stock" in product_columns:
        op.execute(
            sa.text(
                """
                UPDATE inventory AS i
                SET minimum_stock = COALESCE(p.minimum_stock, 0)
                FROM product_variants AS v
                JOIN products AS p ON p.id = v.product_id
                WHERE i.variant_id = v.id
                """
            )
        )
        op.drop_column("products", "minimum_stock")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    product_columns = {column["name"] for column in inspector.get_columns("products")}
    if "minimum_stock" not in product_columns:
        op.add_column("products", sa.Column("minimum_stock", sa.Integer(), nullable=False, server_default="0"))
    inventory_columns = {column["name"] for column in inspect(bind).get_columns("inventory")}
    if "minimum_stock" in inventory_columns:
        op.drop_constraint("ck_inventory_minimum_stock_non_negative", "inventory", type_="check")
        op.drop_column("inventory", "minimum_stock")
