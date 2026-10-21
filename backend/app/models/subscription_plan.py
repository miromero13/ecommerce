from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class SubscriptionPlan(Base):
    __tablename__ = "saas_plans"

    id = Column(String(50), primary_key=True)  # e.g. plan_basic, plan_pro, plan_enterprise
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(String(500), nullable=True)
    price_monthly = Column(Numeric(10, 2), nullable=False, default=0.0)
    price_yearly = Column(Numeric(10, 2), nullable=False, default=0.0)
    max_branches = Column(Integer, nullable=False, default=2)
    max_garments = Column(Integer, nullable=False, default=500)
    features = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, nullable=False, default=True)

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

    subscriptions = relationship(
        "TenantSubscription",
        back_populates="plan",
        cascade="all, delete-orphan",
    )
