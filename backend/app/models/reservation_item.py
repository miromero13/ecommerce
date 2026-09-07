import uuid

from sqlalchemy import Column, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ReservationItem(Base):
    __tablename__ = "reservation_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    reservation_id = Column(UUID(as_uuid=True), ForeignKey("reservations.id"), nullable=False, index=True)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    reservation = relationship("Reservation", back_populates="items")
    variant = relationship("ProductVariant")

    __table_args__ = (UniqueConstraint("reservation_id", "variant_id", name="uq_reservation_item_reservation_variant"),)
