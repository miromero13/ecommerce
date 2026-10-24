"""Allow customer-owned empty carts before company selection.

Revision ID: 0040
Revises: 0039
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0040"
down_revision = "0039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("carts", "tenant_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)


def downgrade() -> None:
    # Lock before checking so a concurrent empty-cart insert cannot race SET NOT NULL.
    op.execute("LOCK TABLE carts IN ACCESS EXCLUSIVE MODE")
    if op.get_bind().execute(sa.text("SELECT EXISTS (SELECT 1 FROM carts WHERE tenant_id IS NULL)")).scalar():
        raise RuntimeError("Cannot downgrade 0040: customer carts without a company still exist")
    op.alter_column("carts", "tenant_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
