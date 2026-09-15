"""add product discounts

Revision ID: 0021
 Revises: 0020
"""

from alembic import op
import sqlalchemy as sa


revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("discount_type", sa.String(length=20), nullable=True))
    op.add_column("products", sa.Column("discount_value", sa.Numeric(precision=10, scale=2), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "discount_value")
    op.drop_column("products", "discount_type")
