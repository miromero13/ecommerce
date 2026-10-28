"""CU1 multi-tenant: category, season and collection names are unique per company, not platform-wide.

Before, a second company could not create "Vestidos" because another company already had it.

Revision ID: 0051
Revises: 0050
"""
from alembic import op

revision = "0051"
down_revision = "0050"
branch_labels = None
depends_on = None

TABLES = ("categories", "seasons", "collections")


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {table}_name_key")
        op.create_unique_constraint(f"uq_{table}_tenant_name", table, ["tenant_id", "name"])


def downgrade() -> None:
    for table in TABLES:
        op.drop_constraint(f"uq_{table}_tenant_name", table, type_="unique")
        op.create_unique_constraint(f"{table}_name_key", table, ["name"])
