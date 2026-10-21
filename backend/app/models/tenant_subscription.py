from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import Column, DateTime, Enum as SQLAlchemyEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.schemas.enums import (
    BillingCycleEnum,
    SubscriptionPaymentMethodEnum,
    SubscriptionStatusEnum,
)


class TenantSubscription(Base):
    __tablename__ = "tenant_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id = Column(
        String(50),
        ForeignKey("saas_plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    billing_cycle = Column(
        SQLAlchemyEnum(BillingCycleEnum, name="billingcycleenum"),
        nullable=False,
        default=BillingCycleEnum.monthly,
    )
    status = Column(
        SQLAlchemyEnum(SubscriptionStatusEnum, name="subscriptionstatusenum"),
        nullable=False,
        default=SubscriptionStatusEnum.active,
        index=True,
    )
    payment_method = Column(
        SQLAlchemyEnum(SubscriptionPaymentMethodEnum, name="subscriptionpaymentmethodenum"),
        nullable=False,
        default=SubscriptionPaymentMethodEnum.simulated_card,
    )
    start_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    end_date = Column(
        DateTime(timezone=True),
        nullable=True,
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

    tenant = relationship("Tenant", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")


# Cross-references
from app.models.tenant import Tenant  # noqa: E402, F401
from app.models.subscription_plan import SubscriptionPlan  # noqa: E402, F401
