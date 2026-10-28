import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SuggestionStatusEnum(str, enum.Enum):
    pending = "pending"
    applied = "applied"
    discarded = "discarded"


class ExpertReplenishmentRule(Base):
    __tablename__ = "expert_replenishment_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    lookback_days = Column(Integer, default=7, nullable=False)
    coverage_days = Column(Integer, default=14, nullable=False)
    is_auto_enabled = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    tenant = relationship(
        "Tenant",
        back_populates="expert_replenishment_rule",
        passive_deletes=True,
    )


class ExpertTransferSuggestion(Base):
    __tablename__ = "expert_transfer_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("product_variants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_branch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_branch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    suggested_quantity = Column(Integer, nullable=False, default=0)
    reason = Column(Text, nullable=False)
    status = Column(String(32), default=SuggestionStatusEnum.pending.value, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    applied_at = Column(DateTime(timezone=True), nullable=True)

    tenant = relationship(
        "Tenant",
        back_populates="expert_transfer_suggestions",
        passive_deletes=True,
    )
    variant = relationship("ProductVariant", foreign_keys=[variant_id])
    source_branch = relationship("Branch", foreign_keys=[source_branch_id])
    target_branch = relationship("Branch", foreign_keys=[target_branch_id])
