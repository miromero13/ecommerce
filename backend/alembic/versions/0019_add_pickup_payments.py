"""add pickup payments

Revision ID: 0019_add_pickup_payments
Revises: 0018_add_sales
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ENUM as PG_ENUM


revision = "0019_add_pickup_payments"
down_revision = "0018_add_sales"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    fulfillment_status = PG_ENUM(
        "pending_pickup", "ready_for_pickup", "collected", "expired", "cancelled",
        name="fulfillmentstatusenum", create_type=False,
    )
    fulfillment_status.create(bind, checkfirst=True)
    op.execute("ALTER TYPE cartstatusenum ADD VALUE IF NOT EXISTS 'checkout_pending'")
    op.add_column("orders", sa.Column("pickup_branch_id", UUID(as_uuid=True), nullable=True))
    op.add_column("orders", sa.Column("pickup_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("orders", sa.Column("pickup_code", sa.String(), nullable=True))
    op.add_column("orders", sa.Column("fulfillment_status", fulfillment_status, nullable=True))
    op.create_foreign_key("fk_orders_pickup_branch", "orders", "branches", ["pickup_branch_id"], ["id"])
    op.create_unique_constraint("uq_orders_pickup_code", "orders", ["pickup_code"])
    op.create_table(
        "payment_attempts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("order_id", UUID(as_uuid=True), nullable=False),
        sa.Column("cart_id", UUID(as_uuid=True), nullable=False),
        sa.Column("stripe_payment_intent_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["cart_id"], ["carts.id"]),
        sa.UniqueConstraint("stripe_payment_intent_id", name="uq_payment_attempts_intent"),
        sa.UniqueConstraint("idempotency_key", name="uq_payment_attempts_idempotency"),
    )
    op.create_table(
        "stripe_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("stripe_event_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("stripe_event_id", name="uq_stripe_events_event"),
    )


def downgrade() -> None:
    op.drop_table("stripe_events")
    op.drop_table("payment_attempts")
    op.drop_constraint("uq_orders_pickup_code", "orders", type_="unique")
    op.drop_constraint("fk_orders_pickup_branch", "orders", type_="foreignkey")
    op.drop_column("orders", "fulfillment_status")
    op.drop_column("orders", "pickup_code")
    op.drop_column("orders", "pickup_expires_at")
    op.drop_column("orders", "pickup_branch_id")
    op.execute("DROP TYPE IF EXISTS fulfillmentstatusenum")
