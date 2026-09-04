"""cleanup legacy catalog columns

Revision ID: 0010_cleanup_catalog
Revises: 0009_add_product_variants
Create Date: 2026-09-04 01:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID


revision = "0010_cleanup_catalog"
down_revision = "0009_add_product_variants"
branch_labels = None
depends_on = None


def _drop_fk_constraints(bind, table_name: str, columns: set[str]) -> None:
    inspector = inspect(bind)
    for fk in inspector.get_foreign_keys(table_name):
        constrained = set(fk.get("constrained_columns") or [])
        if constrained & columns and fk.get("name"):
            try:
                op.drop_constraint(fk["name"], table_name, type_="foreignkey")
            except Exception:
                pass


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("inventory"):
        _drop_fk_constraints(bind, "inventory", {"product_id"})
        columns = {column["name"] for column in inspector.get_columns("inventory")}
        if "product_id" in columns:
            op.drop_column("inventory", "product_id")

    if inspector.has_table("products"):
        _drop_fk_constraints(bind, "products", {"size_id", "color_id"})
        columns = {column["name"] for column in inspector.get_columns("products")}
        for column in ["sku", "status", "size_id", "color_id"]:
            if column in columns:
                op.drop_column("products", column)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("products"):
        columns = {column["name"] for column in inspector.get_columns("products")}
        if "sku" not in columns:
            op.add_column("products", sa.Column("sku", sa.String(), nullable=True))
        if "status" not in columns:
            op.add_column("products", sa.Column("status", sa.String(), nullable=True))
        if "size_id" not in columns:
            op.add_column("products", sa.Column("size_id", UUID(as_uuid=True), nullable=True))
        if "color_id" not in columns:
            op.add_column("products", sa.Column("color_id", UUID(as_uuid=True), nullable=True))

    if inspector.has_table("inventory"):
        columns = {column["name"] for column in inspector.get_columns("inventory")}
        if "product_id" not in columns:
            op.add_column("inventory", sa.Column("product_id", UUID(as_uuid=True), nullable=True))
