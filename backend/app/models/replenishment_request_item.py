import uuid
from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class ReplenishmentRequestItem(Base):
    __tablename__ = "replenishment_request_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("replenishment_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=False, index=True)
    requested_quantity = Column(Integer, nullable=False)
    request = relationship("ReplenishmentRequest", back_populates="items")
    variant = relationship("ProductVariant")
    __table_args__ = (UniqueConstraint("request_id", "variant_id", name="uq_replenishment_request_variant"), CheckConstraint("requested_quantity > 0", name="ck_replenishment_requested_quantity_positive"))
