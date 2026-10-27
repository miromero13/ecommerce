"""Tenant branding and Stripe Connect fields; impossible stock check constraints.

Revision ID: 0041
Revises: 0040
"""
from alembic import op
import sqlalchemy as sa

revision = "0041"
down_revision = "0040"
branch_labels = None
depends_on = None

STOCK_CHECKS = (
    ("ck_inventory_quantity_non_negative", "quantity >= 0"),
    ("ck_inventory_reserved_non_negative", "reserved_quantity >= 0"),
    ("ck_inventory_reserved_within_quantity", "reserved_quantity <= quantity"),
)


def upgrade() -> None:
    op.add_column("tenants", sa.Column("logo_url", sa.String(500), nullable=True))
    op.add_column("tenants", sa.Column("primary_color", sa.String(7), nullable=True))
    op.add_column("tenants", sa.Column("stripe_account_id", sa.String(64), nullable=True))
    op.add_column("tenants", sa.Column("stripe_charges_enabled", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("tenants", sa.Column("platform_fee_percent", sa.Numeric(5, 2), nullable=False, server_default="0"))
    op.create_unique_constraint("uq_tenants_stripe_account_id", "tenants", ["stripe_account_id"])

    # Clamp rows left impossible by past bugs so the checks can be enforced.
    op.execute("UPDATE inventory SET quantity = GREATEST(quantity, 0)")
    op.execute("UPDATE inventory SET reserved_quantity = LEAST(GREATEST(reserved_quantity, 0), quantity)")
    for name, condition in STOCK_CHECKS:
        op.create_check_constraint(name, "inventory", condition)


def downgrade() -> None:
    for name, _ in STOCK_CHECKS:
        op.drop_constraint(name, "inventory", type_="check")
    op.drop_constraint("uq_tenants_stripe_account_id", "tenants", type_="unique")
    for column in ("platform_fee_percent", "stripe_charges_enabled", "stripe_account_id", "primary_color", "logo_url"):
        op.drop_column("tenants", column)
