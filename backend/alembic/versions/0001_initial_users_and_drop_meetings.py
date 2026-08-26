"""initial users table and drop meetings

Revision ID: 0001_initial_users
Revises:
Create Date: 2026-08-25 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = "0001_initial_users"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("meeting_participants"):
        op.drop_table("meeting_participants")

    if inspector.has_table("meetings"):
        op.drop_table("meetings")

    if not inspector.has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=False, unique=True),
            sa.Column("hashed_password", sa.String(), nullable=False),
            sa.Column(
                "gender",
                sa.Enum("masculino", "femenino", name="genderenum"),
                nullable=False,
            ),
            sa.Column(
                "rol",
                sa.Enum(
                    "administrador",
                    "cliente",
                    "delivery",
                    name="rolenum",
                ),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("users"):
        op.drop_table("users")

    # No recreamos meetings en downgrade porque ya fueron eliminadas del modelo.
