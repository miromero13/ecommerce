"""CU17: loyalty points of a customer, kept per company."""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class LoyaltyAccount(Base):
    __tablename__ = "loyalty_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    points_balance = Column(Integer, nullable=False, default=0)
    lifetime_points = Column(Integer, nullable=False, default=0)  # earned only; decides the tier
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    __table_args__ = (UniqueConstraint("tenant_id", "user_id", name="uq_loyalty_account_tenant_user"),)


class LoyaltyLedger(Base):
    """Every movement of points; (source_type, source_id, type) makes each movement idempotent."""
    __tablename__ = "loyalty_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("loyalty_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(10), nullable=False)  # earn | redeem | refund
    points = Column(Integer, nullable=False)  # always positive; the type gives the sign
    source_type = Column(String(10), nullable=False)  # order | sale
    source_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (UniqueConstraint("source_type", "source_id", "type", name="uq_loyalty_ledger_source_type"),)
