"""add inventory movements

Revision ID: 0014_add_inventory_movements
Revises: 0013_add_product_variant_images
Create Date: 2026-09-07 00:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID


revision = "0014_add_inventory_movements"
down_revision = "0013_add_product_variant_images"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    movement_type_enum = sa.Enum(
        "income",
        "outcome",
        "transfer_in",
        "transfer_out",
        name="inventorymovementtypeenum",
    )

    if not inspector.has_table("inventory_movements"):
        movement_type_enum.create(bind, checkfirst=True)
        op.create_table(
            "inventory_movements",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("variant_id", UUID(as_uuid=True), nullable=False),
            sa.Column("branch_id", UUID(as_uuid=True), nullable=False),
            sa.Column("movement_type", movement_type_enum, nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("reference_branch_id", UUID(as_uuid=True), nullable=True),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("created_by", UUID(as_uuid=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"]),
            sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
            sa.ForeignKeyConstraint(["reference_branch_id"], ["branches.id"]),
            sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("inventory_movements"):
        op.drop_table("inventory_movements")

    movement_type_enum = sa.Enum(
        "income",
        "outcome",
        "transfer_in",
        "transfer_out",
        name="inventorymovementtypeenum",
    )
    movement_type_enum.drop(bind, checkfirst=True)
