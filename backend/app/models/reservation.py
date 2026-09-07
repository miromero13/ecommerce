import uuid

from sqlalchemy import Column, Date, DateTime, Enum as SQLAlchemyEnum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.schemas.reservation_schema import ReservationStatusEnum


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    visit_date = Column(Date, nullable=False, index=True)
    expires_at = Column(Date, nullable=False, index=True)
    status = Column(SQLAlchemyEnum(ReservationStatusEnum, name="reservationstatusenum"), nullable=False, default=ReservationStatusEnum.pending)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    items = relationship("ReservationItem", back_populates="reservation", cascade="all, delete-orphan")
