"""make administrators global

Revision ID: 0025
Revises: 0024
"""

from alembic import op
import sqlalchemy as sa


revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE users SET branch_id = NULL "
            "WHERE rol = 'administrador'"
        )
    )


def downgrade() -> None:
    pass
