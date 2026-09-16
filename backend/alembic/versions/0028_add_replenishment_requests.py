"""add replenishment requests

Revision ID: 0028
Revises: 0027
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM, UUID

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    status_enum = PG_ENUM("requested", "accepted", "preparing", "awaiting_receipt", "delivered", name="replenishmentstatusenum", create_type=False)
    status_enum.create(bind, checkfirst=True)
    op.create_table("replenishment_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True), sa.Column("provider_id", UUID(as_uuid=True), nullable=False), sa.Column("branch_id", UUID(as_uuid=True), nullable=False), sa.Column("requested_by", UUID(as_uuid=True), nullable=False), sa.Column("status", status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("accepted_by", UUID(as_uuid=True)), sa.Column("accepted_at", sa.DateTime(timezone=True)), sa.Column("preparing_by", UUID(as_uuid=True)), sa.Column("preparing_at", sa.DateTime(timezone=True)), sa.Column("awaiting_receipt_by", UUID(as_uuid=True)), sa.Column("awaiting_receipt_at", sa.DateTime(timezone=True)), sa.Column("delivered_by", UUID(as_uuid=True)), sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["provider_id"], ["providers.id"]), sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]), sa.ForeignKeyConstraint(["requested_by"], ["users.id"]), sa.ForeignKeyConstraint(["accepted_by"], ["users.id"]), sa.ForeignKeyConstraint(["preparing_by"], ["users.id"]), sa.ForeignKeyConstraint(["awaiting_receipt_by"], ["users.id"]), sa.ForeignKeyConstraint(["delivered_by"], ["users.id"]))
    for column in ("provider_id", "branch_id", "status"):
        op.create_index(f"ix_replenishment_requests_{column}", "replenishment_requests", [column])
    op.create_table("replenishment_request_items", sa.Column("id", UUID(as_uuid=True), primary_key=True), sa.Column("request_id", UUID(as_uuid=True), nullable=False), sa.Column("variant_id", UUID(as_uuid=True), nullable=False), sa.Column("requested_quantity", sa.Integer(), nullable=False), sa.ForeignKeyConstraint(["request_id"], ["replenishment_requests.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["variant_id"], ["product_variants.id"]), sa.UniqueConstraint("request_id", "variant_id", name="uq_replenishment_request_variant"), sa.CheckConstraint("requested_quantity > 0", name="ck_replenishment_requested_quantity_positive"))
    op.create_index("ix_replenishment_request_items_request_id", "replenishment_request_items", ["request_id"])
    op.create_index("ix_replenishment_request_items_variant_id", "replenishment_request_items", ["variant_id"])

def downgrade() -> None:
    op.drop_table("replenishment_request_items")
    op.drop_table("replenishment_requests")
    op.execute("DROP TYPE IF EXISTS replenishmentstatusenum")
