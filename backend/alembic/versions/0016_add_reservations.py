"""add reservations

Revision ID: 0016_add_reservations
Revises: 0015_add_carts
Create Date: 2026-09-07 02:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID, ENUM as PG_ENUM


revision = "0016_add_reservations"
down_revision = "0015_add_carts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    reservation_status_enum = PG_ENUM(
        "pending",
        "confirmed",
        "attended",
        "cancelled",
        "expired",
        name="reservationstatusenum",
        create_type=False,
    )

    if not inspector.has_table("reservations"):
        reservation_status_enum.create(bind, checkfirst=True)
        op.create_table(
            "reservations",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("branch_id", UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", UUID(as_uuid=True), nullable=False),
            sa.Column("visit_date", sa.Date(), nullable=False),
            sa.Column("expires_at", sa.Date(), nullable=False),
            sa.Column("status", reservation_status_enum, nullable=False),
            sa.Column("total_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        )

    if not inspector.has_table("reservation_items"):
        op.create_table(
            "reservation_items",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("reservation_id", UUID(as_uuid=True), nullable=False),
            sa.Column("variant_id", UUID(as_uuid=True), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
            sa.ForeignKeyConstraint(["reservation_id"], ["reservations.id"]),
            sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"]),
            sa.UniqueConstraint("reservation_id", "variant_id", name="uq_reservation_item_reservation_variant"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("reservation_items"):
        op.drop_table("reservation_items")
    if inspector.has_table("reservations"):
        op.drop_table("reservations")

    op.execute("DROP TYPE IF EXISTS reservationstatusenum")
