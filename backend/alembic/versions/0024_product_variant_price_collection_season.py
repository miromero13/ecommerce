"""keep product price and season on variants and collections

Revision ID: 0024
Revises: 0023
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None


def _drop_product_foreign_keys(columns: set[str]) -> None:
    bind = op.get_bind()
    for foreign_key in inspect(bind).get_foreign_keys("products"):
        if set(foreign_key.get("constrained_columns") or []) & columns and foreign_key.get("name"):
            op.drop_constraint(foreign_key["name"], "products", type_="foreignkey")


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("products")}
    _drop_product_foreign_keys({"season_id"})
    if "price" in columns:
        op.drop_column("products", "price")
    if "season_id" in columns:
        op.drop_column("products", "season_id")


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("products")}
    if "price" not in columns:
        op.add_column("products", sa.Column("price", sa.Numeric(10, 2), nullable=True))
    if "season_id" not in columns:
        op.add_column("products", sa.Column("season_id", postgresql.UUID(as_uuid=True), nullable=True))

    op.create_foreign_key("fk_products_season_id", "products", "seasons", ["season_id"], ["id"])
