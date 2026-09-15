"""add product minimum stock

Revision ID: 0026
Revises: 0025
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("products")}
    if "minimum_stock" not in columns:
        op.add_column("products", sa.Column("minimum_stock", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("products")}
    if "minimum_stock" in columns:
        op.drop_column("products", "minimum_stock")
