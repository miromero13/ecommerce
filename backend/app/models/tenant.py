from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLAlchemyEnum, Numeric, String
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
    primary_color = Column(String(7), nullable=True)
    # Stripe Connect: each company is paid into its own connected account.
    stripe_account_id = Column(String(64), nullable=True, unique=True)
    stripe_charges_enabled = Column(Boolean, nullable=False, default=False, server_default="false")
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


# Register the related mappers whenever the Tenant model is imported.
from app.models.user import User  # noqa: E402, F401
from app.models.branch import Branch  # noqa: E402, F401
from app.models.tenant_subscription import TenantSubscription  # noqa: E402, F401

