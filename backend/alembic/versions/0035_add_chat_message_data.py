"""persist catalog cards in chatbot messages"""

from alembic import op
import sqlalchemy as sa


revision = "0035"
down_revision = "0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("conversation_messages", sa.Column("message_data", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("conversation_messages", "message_data")
