"""CU18: gift cards with unique alphanumeric code, balance, QR code and recipient."""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class GiftCard(Base):
    __tablename__ = "gift_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True)
    buyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    code = Column(String(32), nullable=False, unique=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    balance = Column(Numeric(10, 2), nullable=False)
    recipient_name = Column(String(120), nullable=False)
    recipient_email = Column(String(255), nullable=False, index=True)
    custom_message = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="active", server_default="active")  # active | redeemed | expired
    payment_method = Column(String(30), nullable=False, default="stripe", server_default="stripe")
    stripe_payment_intent_id = Column(String(120), nullable=True)
    qr_code_url = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    redeemed_at = Column(DateTime(timezone=True), nullable=True)
    redeemed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    buyer = relationship("User", foreign_keys=[buyer_id])
    redeemed_by = relationship("User", foreign_keys=[redeemed_by_id])
