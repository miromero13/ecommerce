import uuid

from sqlalchemy import Column, DateTime, Enum as SQLAlchemyEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.schemas.inventory_schema import InventoryMovementTypeEnum


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False, index=True)
    movement_type = Column(SQLAlchemyEnum(InventoryMovementTypeEnum, name="inventorymovementtypeenum"), nullable=False)
    quantity = Column(Integer, nullable=False)
    reference_branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True, index=True)
    note = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    variant = relationship("ProductVariant")
    branch = relationship("Branch", foreign_keys=[branch_id])
    reference_branch = relationship("Branch", foreign_keys=[reference_branch_id])
    creator = relationship("User")
