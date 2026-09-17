"""add collaborative recommendations

Revision ID: 0031
Revises: 0030
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID


revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    if not inspector.has_table("user_product_interactions"):
        op.create_table(
            "user_product_interactions",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", UUID(as_uuid=True), nullable=False),
            sa.Column("product_id", UUID(as_uuid=True), nullable=False),
            sa.Column("interaction_type", sa.String(length=32), nullable=False),
            sa.Column("weight", sa.Integer(), nullable=False),
            sa.Column("order_id", UUID(as_uuid=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
            sa.UniqueConstraint("order_id", "product_id", "interaction_type", name="uq_interaction_order_product_type"),
        )
        op.create_index("ix_user_product_interactions_user_id", "user_product_interactions", ["user_id"])
        op.create_index("ix_user_product_interactions_product_id", "user_product_interactions", ["product_id"])
        op.create_index("ix_user_product_interactions_order_id", "user_product_interactions", ["order_id"])
        op.create_index("ix_user_product_interactions_interaction_type", "user_product_interactions", ["interaction_type"])
    if not inspector.has_table("collaborative_embeddings"):
        op.create_table(
            "collaborative_embeddings",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("subject_type", sa.String(length=16), nullable=False),
            sa.Column("subject_id", UUID(as_uuid=True), nullable=False),
            sa.Column("vector", sa.Text(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.UniqueConstraint("subject_type", "subject_id", name="uq_collaborative_embedding_subject"),
        )


def downgrade() -> None:
    inspector = inspect(op.get_bind())
    if inspector.has_table("collaborative_embeddings"):
        op.drop_table("collaborative_embeddings")
    if inspector.has_table("user_product_interactions"):
        op.drop_table("user_product_interactions")
