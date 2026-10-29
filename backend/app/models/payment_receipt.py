"""Simple payment receipt (comprobante): one per payment transaction, PDF and emailed to the payer."""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.core.database import Base


class PaymentReceipt(Base):
    __tablename__ = "payment_receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # The company that sold (or, for a subscription, the company that paid the platform).
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    issuer = Column(String(10), nullable=False)  # company | platform (subscriptions)
    series = Column(String(40), nullable=False)  # numbering sequence: the company id, or "platform"
    number = Column(Integer, nullable=False)
    kind = Column(String(20), nullable=False)  # order | sale | reservation_deposit | subscription
    source_id = Column(UUID(as_uuid=True), nullable=False)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    customer_name = Column(String(150), nullable=True)
    customer_email = Column(String(255), nullable=True)
    payment_method = Column(String(10), nullable=False)  # card | qr | cash
    currency = Column(String(10), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    lines = Column(JSONB, nullable=False)  # [{description, quantity, unit_price, total}]
    summary = Column(JSONB, nullable=False)  # [{label, amount}] e.g. subtotal, discounts, cash received, change
    issued_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    emailed_at = Column(DateTime(timezone=True), nullable=True)
    email_attempts = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("series", "number", name="uq_payment_receipts_series_number"),
        UniqueConstraint("kind", "source_id", name="uq_payment_receipts_source"),
    )
