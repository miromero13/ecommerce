import uuid
from sqlalchemy import Column, DateTime, Enum as SQLAlchemyEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from app.schemas.replenishment_schema import ReplenishmentStatusEnum

class ReplenishmentRequest(Base):
    __tablename__ = "replenishment_requests"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False, index=True)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(SQLAlchemyEnum(ReplenishmentStatusEnum, name="replenishmentstatusenum"), nullable=False, default=ReplenishmentStatusEnum.requested, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    accepted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    preparing_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    preparing_at = Column(DateTime(timezone=True), nullable=True)
    awaiting_receipt_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    awaiting_receipt_at = Column(DateTime(timezone=True), nullable=True)
    delivered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    items = relationship("ReplenishmentRequestItem", back_populates="request", cascade="all, delete-orphan")
