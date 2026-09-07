import uuid

from sqlalchemy import Column, DateTime, Enum as SQLAlchemyEnum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.schemas.order_schema import OrderStatusEnum, PaymentMethodEnum, PaymentStatusEnum


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(SQLAlchemyEnum(OrderStatusEnum, name="orderstatusenum"), nullable=False, default=OrderStatusEnum.pending)
    payment_method = Column(SQLAlchemyEnum(PaymentMethodEnum, name="paymentmethodenum"), nullable=False)
    payment_status = Column(SQLAlchemyEnum(PaymentStatusEnum, name="paymentstatusenum"), nullable=False, default=PaymentStatusEnum.pending)
    stripe_payment_intent_id = Column(String, nullable=True, index=True)
    cash_reference = Column(String, nullable=True)
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    currency = Column(String, nullable=False, default="usd")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
