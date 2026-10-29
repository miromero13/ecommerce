"""Add expert replenishment rules and transfer suggestions tables.

Revision ID: 0043
Revises: 0042
"""
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0043"
down_revision = "0042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "expert_replenishment_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("lookback_days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("coverage_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("is_auto_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_expert_replenishment_rules_id",
        "expert_replenishment_rules",
        ["id"],
    )
    op.create_index(
        "ix_expert_replenishment_rules_tenant_id",
        "expert_replenishment_rules",
        ["tenant_id"],
    )

    op.create_table(
        "expert_transfer_suggestions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "variant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("product_variants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_branch_id",
            UUID(as_uuid=True),
            sa.ForeignKey("branches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_branch_id",
            UUID(as_uuid=True),
            sa.ForeignKey("branches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("suggested_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_expert_transfer_suggestions_id",
        "expert_transfer_suggestions",
        ["id"],
    )
    op.create_index(
        "ix_expert_transfer_suggestions_tenant_id",
        "expert_transfer_suggestions",
        ["tenant_id"],
    )
    op.create_index(
        "ix_expert_transfer_suggestions_variant_id",
        "expert_transfer_suggestions",
        ["variant_id"],
    )
    op.create_index(
        "ix_expert_transfer_suggestions_status",
        "expert_transfer_suggestions",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_expert_transfer_suggestions_status", table_name="expert_transfer_suggestions")
    op.drop_index("ix_expert_transfer_suggestions_variant_id", table_name="expert_transfer_suggestions")
    op.drop_index("ix_expert_transfer_suggestions_tenant_id", table_name="expert_transfer_suggestions")
    op.drop_index("ix_expert_transfer_suggestions_id", table_name="expert_transfer_suggestions")
    op.drop_table("expert_transfer_suggestions")

    op.drop_index("ix_expert_replenishment_rules_tenant_id", table_name="expert_replenishment_rules")
    op.drop_index("ix_expert_replenishment_rules_id", table_name="expert_replenishment_rules")
    op.drop_table("expert_replenishment_rules")
