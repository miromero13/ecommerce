"""link reservation items to carts and orders

Revision ID: 0023
 Revises: 0022
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reservations", sa.Column("cart_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_reservations_cart_id", "reservations", "carts", ["cart_id"], ["id"])
    op.create_index("ix_reservations_cart_id", "reservations", ["cart_id"], unique=True)

    op.add_column("cart_items", sa.Column("reservation_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_cart_items_reservation_id", "cart_items", "reservations", ["reservation_id"], ["id"])
    op.create_index("ix_cart_items_reservation_id", "cart_items", ["reservation_id"])

    op.add_column("order_items", sa.Column("reservation_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_order_items_reservation_id", "order_items", "reservations", ["reservation_id"], ["id"])
    op.create_index("ix_order_items_reservation_id", "order_items", ["reservation_id"])


def downgrade() -> None:
    op.drop_index("ix_order_items_reservation_id", table_name="order_items")
    op.drop_constraint("fk_order_items_reservation_id", "order_items", type_="foreignkey")
    op.drop_column("order_items", "reservation_id")
    op.drop_index("ix_cart_items_reservation_id", table_name="cart_items")
    op.drop_constraint("fk_cart_items_reservation_id", "cart_items", type_="foreignkey")
    op.drop_column("cart_items", "reservation_id")
    op.drop_index("ix_reservations_cart_id", table_name="reservations")
    op.drop_constraint("fk_reservations_cart_id", "reservations", type_="foreignkey")
    op.drop_column("reservations", "cart_id")
