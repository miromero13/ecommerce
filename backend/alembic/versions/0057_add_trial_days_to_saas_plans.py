"""Add trial_days to saas_plans table.

Revision ID: 0057
Revises: 0056
Create Date: 2026-11-12
"""

from alembic import op
import sqlalchemy as sa

revision = "0057"
down_revision = "0056"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "saas_plans",
        sa.Column("trial_days", sa.Integer(), server_default="90", nullable=False),
    )
    # Ensure all existing plans have 90 days trial by default
    op.execute("UPDATE saas_plans SET trial_days = 90 WHERE trial_days IS NULL")


def downgrade() -> None:
    op.drop_column("saas_plans", "trial_days")
