import uuid

from sqlalchemy import Column, DateTime, Enum as SQLAlchemyEnum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.schemas.order_schema import FulfillmentStatusEnum, OrderStatusEnum, PaymentMethodEnum, PaymentStatusEnum


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    promotion_code_id = Column(UUID(as_uuid=True), ForeignKey("promotion_codes.id"), nullable=True, index=True)
    status = Column(SQLAlchemyEnum(OrderStatusEnum, name="orderstatusenum"), nullable=False, default=OrderStatusEnum.pending)
    payment_method = Column(SQLAlchemyEnum(PaymentMethodEnum, name="paymentmethodenum"), nullable=False)
    payment_status = Column(SQLAlchemyEnum(PaymentStatusEnum, name="paymentstatusenum"), nullable=False, default=PaymentStatusEnum.pending)
    stripe_payment_intent_id = Column(String, nullable=True, index=True)
    cash_reference = Column(String, nullable=True)
    pickup_branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True, index=True)
    pickup_expires_at = Column(DateTime(timezone=True), nullable=True)
    pickup_code = Column(String, nullable=True, unique=True)
    fulfillment_status = Column(SQLAlchemyEnum(FulfillmentStatusEnum, name="fulfillmentstatusenum"), nullable=True)
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    # CU20 delivery: platform drivers (no company) take ready orders from any company.
    fulfillment_type = Column(String(10), nullable=False, default="pickup", server_default="pickup")  # pickup | delivery
    delivery_address = Column(String(255), nullable=True)
    delivery_reference = Column(String(255), nullable=True)
    delivery_latitude = Column(Numeric(9, 6), nullable=True)
    delivery_longitude = Column(Numeric(9, 6), nullable=True)
    delivery_distance_km = Column(Numeric(6, 2), nullable=True)
    shipping_cost = Column(Numeric(10, 2), nullable=False, default=0, server_default="0")
    delivery_pin = Column(String(4), nullable=True)
    delivery_driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    currency = Column(String, nullable=False, default="usd")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
