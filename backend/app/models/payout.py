"""Platform collection: every online payment lands in the platform account, is
recorded per company here, and is paid out to the company in a daily settlement."""
import uuid

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    period_date = Column(Date, nullable=False)
    gross_amount = Column(Numeric(10, 2), nullable=False)
    fee_amount = Column(Numeric(10, 2), nullable=False)
    net_amount = Column(Numeric(10, 2), nullable=False)
    transactions_count = Column(Integer, nullable=False)
    currency = Column(String(10), nullable=False)
    status = Column(String(10), nullable=False, default="pending", server_default="pending")  # pending | paid
    # Bank account snapshot at settlement time; later edits never redirect an issued settlement.
    bank_name = Column(String(120), nullable=True)
    bank_account_number = Column(String(40), nullable=True)
    bank_account_holder = Column(String(160), nullable=True)
    transfer_reference = Column(String(120), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    paid_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("tenant_id", "period_date", name="uq_settlements_tenant_period"),)


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(30), nullable=False)  # order | sale | reservation_deposit
    source_id = Column(UUID(as_uuid=True), nullable=False)
    method = Column(String(10), nullable=False)  # card | qr
    gross_amount = Column(Numeric(10, 2), nullable=False)
    fee_amount = Column(Numeric(10, 2), nullable=False)
    net_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False)
    provider_reference = Column(String(120), nullable=True)
    settlement_id = Column(UUID(as_uuid=True), ForeignKey("settlements.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("source_type", "source_id", name="uq_payment_transactions_source"),)


class QrPayment(Base):
    __tablename__ = "qr_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    reference = Column(String(40), nullable=False, unique=True)
    purpose = Column(String(30), nullable=False)  # order | sale | reservation_deposit
    source_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # sale: set when the sale is created
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), nullable=False)
    status = Column(String(10), nullable=False, default="pending", server_default="pending")  # pending | paid | used | expired
    expires_at = Column(DateTime(timezone=True), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
