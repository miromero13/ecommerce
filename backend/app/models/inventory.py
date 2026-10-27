from sqlalchemy import CheckConstraint, Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
import uuid


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    reserved_quantity = Column(Integer, nullable=False, default=0)
    minimum_stock = Column(Integer, nullable=False, default=0)

    variant = relationship("ProductVariant", back_populates="inventory")

    __table_args__ = (
        UniqueConstraint("variant_id", "branch_id", name="uq_inventory_variant_branch"),
        CheckConstraint("minimum_stock >= 0", name="ck_inventory_minimum_stock_non_negative"),
        CheckConstraint("quantity >= 0", name="ck_inventory_quantity_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="ck_inventory_reserved_non_negative"),
        CheckConstraint("reserved_quantity <= quantity", name="ck_inventory_reserved_within_quantity"),
    )
