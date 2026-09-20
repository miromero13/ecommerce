"""persist garment calibration points on product variants"""

from alembic import op
import sqlalchemy as sa


revision = "0036"
down_revision = "0035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("product_variants", sa.Column("garment_points", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("product_variants", "garment_points")
