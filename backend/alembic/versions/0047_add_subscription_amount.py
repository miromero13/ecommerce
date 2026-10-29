"""CU2: amount paid for each subscription period (payment history).

Revision ID: 0047
Revises: 0046
"""
from alembic import op
import sqlalchemy as sa

revision = "0047"
down_revision = "0046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenant_subscriptions", sa.Column("amount", sa.Numeric(10, 2), nullable=True))
    # Existing periods: the plan price for their billing cycle (prices did not store history before).
    op.execute(
        """
        UPDATE tenant_subscriptions ts
        SET amount = CASE WHEN ts.billing_cycle = 'yearly' THEN p.price_yearly ELSE p.price_monthly END
        FROM saas_plans p
        WHERE p.id = ts.plan_id
        """
    )


def downgrade() -> None:
    op.drop_column("tenant_subscriptions", "amount")
