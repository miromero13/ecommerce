import uuid

from sqlalchemy import Column, DateTime, Enum as SQLAlchemyEnum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.schemas.order_schema import PaymentMethodEnum, PaymentStatusEnum
from app.schemas.sales_schema import SaleStatusEnum


class Sale(Base):
    __tablename__ = "sales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    reservation_id = Column(UUID(as_uuid=True), ForeignKey("reservations.id"), nullable=True, unique=True, index=True)
    status = Column(SQLAlchemyEnum(SaleStatusEnum, name="salestatusenum"), nullable=False, default=SaleStatusEnum.completed)
    payment_method = Column(SQLAlchemyEnum(PaymentMethodEnum, name="paymentmethodenum"), nullable=False)
    payment_status = Column(SQLAlchemyEnum(PaymentStatusEnum, name="paymentstatusenum"), nullable=False, default=PaymentStatusEnum.paid)
    cash_reference = Column(String, nullable=True)
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    currency = Column(String, nullable=False, default="usd")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
