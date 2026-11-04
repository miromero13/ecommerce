"""CU21 & CU24: RMA (Return Merchandise Authorization) requests, items, and inspection tracking."""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.branch import Branch
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product_variant import ProductVariant
from app.models.tenant import Tenant
from app.models.user import User


class RmaRequest(Base):
    __tablename__ = "rma_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rma_number = Column(String(32), nullable=False, unique=True, index=True)
    status = Column(String(30), nullable=False, default="pending_inspection")  # pending_inspection | approved | partially_approved | rejected | completed
    customer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    tenant = relationship("Tenant")
    order = relationship("Order")
    user = relationship("User")
    items = relationship("RmaRequestItem", back_populates="rma", cascade="all, delete-orphan", order_by="RmaRequestItem.created_at")


class RmaRequestItem(Base):
    __tablename__ = "rma_request_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    rma_id = Column(UUID(as_uuid=True), ForeignKey("rma_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    order_item_id = Column(UUID(as_uuid=True), ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    reason = Column(String(30), nullable=False)  # wrong_size | wrong_color | factory_defect | change_of_mind
    preferred_resolution = Column(String(30), nullable=False)  # exchange | store_credit
    requested_variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_notes = Column(Text, nullable=True)

    # Review / Physical Inspection fields
    item_condition = Column(String(30), nullable=True)  # intact | factory_damaged | customer_damaged
    action = Column(String(30), nullable=True)  # restock_available | scrap_quarantine | return_to_customer
    status = Column(String(30), nullable=False, default="pending")  # pending | approved_exchange | approved_refund | rejected
    replacement_variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id", ondelete="SET NULL"), nullable=True, index=True)
    inspection_notes = Column(Text, nullable=True)
    quarantine_record = Column(String(64), nullable=True, index=True)

    # Inventory movements linked
    restock_movement_id = Column(UUID(as_uuid=True), ForeignKey("inventory_movements.id", ondelete="SET NULL"), nullable=True)
    dispatch_movement_id = Column(UUID(as_uuid=True), ForeignKey("inventory_movements.id", ondelete="SET NULL"), nullable=True)

    # Financial / Settlement
    refund_amount = Column(Numeric(10, 2), nullable=True)
    wallet_settlement_date = Column(DateTime(timezone=True), nullable=True)
    settlement_status = Column(String(30), nullable=True)  # pending_month_end | settled

    inspected_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    inspected_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    rma = relationship("RmaRequest", back_populates="items")
    order_item = relationship("OrderItem")
    requested_variant = relationship("ProductVariant", foreign_keys=[requested_variant_id])
    replacement_variant = relationship("ProductVariant", foreign_keys=[replacement_variant_id])
    branch = relationship("Branch", foreign_keys=[branch_id])
    inspector = relationship("User", foreign_keys=[inspected_by])
