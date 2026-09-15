"""add reservation outcome statuses

Revision ID: 0020
Revises: 0019_add_pickup_payments
"""

from alembic import op


revision = "0020"
down_revision = "0019_add_pickup_payments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for value in ("purchase_pending", "sold", "not_sold"):
        op.execute(f"ALTER TYPE reservationstatusenum ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    # PostgreSQL does not safely remove enum values while rows may use them.
    pass
