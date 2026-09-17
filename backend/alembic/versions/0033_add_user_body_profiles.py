"""add customer body profiles for the chatbot"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_body_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("top_size", sa.String(length=32), nullable=True),
        sa.Column("bottom_size", sa.String(length=32), nullable=True),
        sa.Column("shoe_size", sa.String(length=32), nullable=True),
        sa.Column("body_shape", sa.String(length=64), nullable=True),
        sa.Column("fit_preference", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_user_body_profiles_user_id"),
    )
    op.create_index("ix_user_body_profiles_user_id", "user_body_profiles", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_body_profiles_user_id", table_name="user_body_profiles")
    op.drop_table("user_body_profiles")
