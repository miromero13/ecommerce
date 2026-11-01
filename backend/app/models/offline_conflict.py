import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.core.database import Base


class OfflineSaleConflict(Base):
    """CU30: an offline cash sale the server could not confirm (usually: no stock left).

    The customer already paid in cash, so the money is tracked here until a person
    resolves it: cash refund, wallet credit (+10%), exchange for another garment, or
    'delivered' (the garment already left the store: the sale stands and stock is adjusted).
    """

    __tablename__ = "offline_sale_conflicts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False, index=True)
    cashier_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    cash_session_id = Column(UUID(as_uuid=True), ForeignKey("cash_sessions.id", ondelete="SET NULL"), nullable=True)
    operation_id = Column(String(64), nullable=False, unique=True, index=True)  # client UUID: idempotency key
    receipt_number = Column(String(40), nullable=False)
    reason = Column(String(255), nullable=False)
    items = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)  # [{variant_id, sku, product_name, quantity, unit_price}]
    subtotal = Column(Numeric(10, 2), nullable=False)
    discount = Column(Numeric(10, 2), nullable=False, default=0)
    total = Column(Numeric(10, 2), nullable=False)  # cash the customer paid
    cash_received = Column(Numeric(10, 2), nullable=True)
    change_returned = Column(Numeric(10, 2), nullable=True)
    customer_name = Column(String(120), nullable=True)
    customer_phone = Column(String(40), nullable=True)
    customer_email = Column(String(255), nullable=True)
    offline_created_at = Column(DateTime(timezone=True), nullable=True)  # when the sale happened at the till

    status = Column(String(12), nullable=False, default="pending", index=True)  # pending | resolved
    resolution = Column(String(20), nullable=True)  # cash_refund | wallet_credit | exchange | delivered
    refund_amount = Column(Numeric(10, 2), nullable=True)  # cash returned to the customer
    wallet_credit_amount = Column(Numeric(10, 2), nullable=True)  # credited to the customer's wallet
    extra_charged = Column(Numeric(10, 2), nullable=True)  # exchange for a pricier garment
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id", ondelete="SET NULL"), nullable=True)
    refund_receipt_number = Column(String(48), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
