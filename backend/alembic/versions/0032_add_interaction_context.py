"""add variant and branch context to recommendation interactions"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("user_product_interactions", sa.Column("variant_id", UUID(as_uuid=True), nullable=True))
    op.add_column("user_product_interactions", sa.Column("branch_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_interaction_variant", "user_product_interactions", "product_variants", ["variant_id"], ["id"])
    op.create_foreign_key("fk_interaction_branch", "user_product_interactions", "branches", ["branch_id"], ["id"])
    op.create_index("ix_user_product_interactions_variant_id", "user_product_interactions", ["variant_id"])
    op.create_index("ix_user_product_interactions_branch_id", "user_product_interactions", ["branch_id"])


def downgrade() -> None:
    op.drop_index("ix_user_product_interactions_branch_id", table_name="user_product_interactions")
    op.drop_index("ix_user_product_interactions_variant_id", table_name="user_product_interactions")
    op.drop_constraint("fk_interaction_branch", "user_product_interactions", type_="foreignkey")
    op.drop_constraint("fk_interaction_variant", "user_product_interactions", type_="foreignkey")
    op.drop_column("user_product_interactions", "branch_id")
    op.drop_column("user_product_interactions", "variant_id")
