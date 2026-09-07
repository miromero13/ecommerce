"""add product variant images

Revision ID: 0013_add_product_variant_images
Revises: 0012_drop_provider_is_active
Create Date: 2026-09-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0013_add_product_variant_images"
down_revision = "0012_drop_provider_is_active"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("product_variants"):
        columns = {column["name"] for column in inspector.get_columns("product_variants")}
        if "image_url" not in columns:
            op.add_column("product_variants", sa.Column("image_url", sa.String(), nullable=True))
        if "image_public_id" not in columns:
            op.add_column("product_variants", sa.Column("image_public_id", sa.String(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("product_variants"):
        columns = {column["name"] for column in inspector.get_columns("product_variants")}
        if "image_public_id" in columns:
            op.drop_column("product_variants", "image_public_id")
        if "image_url" in columns:
            op.drop_column("product_variants", "image_url")
