"""add provider variant availability

Revision ID: 0027
Revises: 0026
"""

from alembic import op
import sqlalchemy as sa


revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "provider_variant_availability",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("provider_id", sa.UUID(), nullable=False),
        sa.Column("variant_id", sa.UUID(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["provider_id"], ["providers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_id", "variant_id", name="uq_provider_variant_availability"),
        sa.CheckConstraint("quantity >= 0", name="ck_provider_variant_availability_quantity_non_negative"),
    )
    op.create_index("ix_provider_variant_availability_provider_id", "provider_variant_availability", ["provider_id"])
    op.create_index("ix_provider_variant_availability_variant_id", "provider_variant_availability", ["variant_id"])


def downgrade() -> None:
    op.drop_table("provider_variant_availability")
