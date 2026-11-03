"""CU19: store wallet and ledger of transactions for store balance, gift card redemptions, and payments."""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class UserWallet(Base):
    __tablename__ = "user_wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    balance = Column(Numeric(10, 2), nullable=False, default=0.00, server_default="0.00")
    currency = Column(String(10), nullable=False, default="BOB", server_default="BOB")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    user = relationship("User", foreign_keys=[user_id])
    transactions = relationship("WalletTransaction", back_populates="wallet", cascade="all, delete-orphan", order_by="desc(WalletTransaction.created_at)")


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("user_wallets.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(10), nullable=False)  # credit | debit
    amount = Column(Numeric(10, 2), nullable=False)
    balance_after = Column(Numeric(10, 2), nullable=False)
    concept = Column(String(30), nullable=False)  # gift_card_redeem | order_payment | sale_payment | rma_refund
    source_type = Column(String(30), nullable=True)  # gift_card | order | sale | rma
    source_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    wallet = relationship("UserWallet", back_populates="transactions")
