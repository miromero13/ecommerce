"""1P-CU18 cash drawer: each cashier opens their own session in their branch and closes it counting the cash."""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CashSession(Base):
    __tablename__ = "cash_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=False, index=True)
    cashier_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(10), nullable=False, default="open")  # open | closed
    opening_amount = Column(Numeric(10, 2), nullable=False)
    opened_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expected_amount = Column(Numeric(10, 2), nullable=True)  # set at closing
    counted_amount = Column(Numeric(10, 2), nullable=True)
    difference = Column(Numeric(10, 2), nullable=True)  # counted - expected: > 0 surplus, < 0 shortage
    closing_note = Column(String(255), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    movements = relationship("CashMovement", order_by="CashMovement.created_at", lazy="selectin")

    # A cashier has at most one open drawer.
    __table_args__ = (Index("uq_cash_sessions_open_cashier", "cashier_id", unique=True,
                            postgresql_where=text("status = 'open'")),)


class CashMovement(Base):
    __tablename__ = "cash_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("cash_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(12), nullable=False)  # sale | deposit | withdrawal
    method = Column(String(6), nullable=False, default="cash")  # cash | qr (qr never touches the drawer)
    amount = Column(Numeric(10, 2), nullable=False)  # always positive; the type gives the sign
    cash_received = Column(Numeric(10, 2), nullable=True)  # cash sales: what the customer handed over
    change_given = Column(Numeric(10, 2), nullable=True)  # cash sales: change returned
    source_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # sale id
    reason = Column(String(255), nullable=True)  # deposits and withdrawals
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
