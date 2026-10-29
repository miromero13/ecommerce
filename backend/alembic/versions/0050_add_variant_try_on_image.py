"""CU5: transparent garment cut-out used by the virtual fitting rooms (the catalog keeps the model photo).

Revision ID: 0050
Revises: 0049
"""
from alembic import op
import sqlalchemy as sa

revision = "0050"
down_revision = "0049"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("product_variants", sa.Column("try_on_image_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("product_variants", "try_on_image_url")
