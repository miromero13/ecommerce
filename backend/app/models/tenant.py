from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import Column, DateTime, Enum as SQLAlchemyEnum, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.schemas.enums import TenantStatusEnum


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(120), nullable=False, unique=True)
    slug = Column(String(120), nullable=False, unique=True, index=True)
    contact_email = Column(String(255), nullable=False)
    currency = Column(String(10), nullable=False, default="BOB")
    country = Column(String(80), nullable=True, default="Bolivia")
    logo_url = Column(String(500), nullable=True)
    logo_public_id = Column(String(255), nullable=True)  # Cloudinary id, to delete a replaced logo
    primary_color = Column(String(7), nullable=True)
    # Online payments land in the platform account; settlements pay this bank account daily.
    bank_name = Column(String(120), nullable=True)
    bank_account_number = Column(String(40), nullable=True)
    bank_account_holder = Column(String(160), nullable=True)
    platform_fee_percent = Column(Numeric(5, 2), nullable=False, default=0, server_default="0")
    status = Column(
        SQLAlchemyEnum(TenantStatusEnum, name="tenantstatusenum"),
        nullable=False,
        default=TenantStatusEnum.active,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    branches = relationship("Branch", back_populates="tenant", cascade="all, delete-orphan")
    subscriptions = relationship(
        "TenantSubscription",
        back_populates="tenant",
        cascade="all, delete-orphan",
        order_by="desc(TenantSubscription.created_at)",
    )
    expert_replenishment_rule = relationship(
        "ExpertReplenishmentRule",
        back_populates="tenant",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    expert_transfer_suggestions = relationship(
        "ExpertTransferSuggestion",
        back_populates="tenant",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


# Register the related mappers whenever the Tenant model is imported.
from app.models.user import User  # noqa: E402, F401
from app.models.branch import Branch  # noqa: E402, F401
from app.models.tenant_subscription import TenantSubscription  # noqa: E402, F401
from app.models.expert_replenishment import (  # noqa: E402, F401
    ExpertReplenishmentRule,
    ExpertTransferSuggestion,
)

