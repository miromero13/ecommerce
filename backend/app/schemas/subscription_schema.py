from __future__ import annotations

from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.enums import (
    BillingCycleEnum,
    SubscriptionPaymentMethodEnum,
    SubscriptionStatusEnum,
)


class SubscriptionPlanRead(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    price_monthly: float
    price_yearly: float
    max_branches: int
    max_garments: int
    features: List[str]
    is_active: bool

    model_config = {"from_attributes": True}


class SubscriptionPurchaseSimulated(BaseModel):
    # Company / Tenant info
    company_name: str = Field(..., min_length=2, max_length=120)
    slug: Optional[str] = Field(None, min_length=2, max_length=120)
    country: Optional[str] = Field(default="Bolivia", max_length=80)
    currency: Optional[str] = Field(default="BOB", max_length=10)

    # Admin user info
    admin_name: str = Field(..., min_length=2, max_length=120)
    admin_email: EmailStr = Field(...)

    # Subscription choice
    plan_id: str = Field(...)
    billing_cycle: BillingCycleEnum = Field(default=BillingCycleEnum.monthly)

    # Simulated card payment details
    card_number: Optional[str] = Field(default="4242424242424242")
    card_holder: Optional[str] = Field(default="Titular Prueba")
    card_exp: Optional[str] = Field(default="12/28")
    card_cvv: Optional[str] = Field(default="123")


class TenantWithSubscriptionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    slug: Optional[str] = Field(None, min_length=2, max_length=120)
    contact_email: EmailStr = Field(...)
    country: Optional[str] = Field(default="Bolivia", max_length=80)
    currency: Optional[str] = Field(default="BOB", max_length=10)
    admin_name: str = Field(..., min_length=2, max_length=120)
    plan_id: str = Field(...)
    billing_cycle: BillingCycleEnum = Field(default=BillingCycleEnum.monthly)
    payment_method: SubscriptionPaymentMethodEnum = Field(
        default=SubscriptionPaymentMethodEnum.cash
    )


class SubscriptionSummaryRead(BaseModel):
    tenant_id: str
    tenant_name: str
    has_active_subscription: bool
    plan: Optional[dict[str, Any]] = None
    subscription: Optional[dict[str, Any]] = None
    usage: dict[str, Any]
    features: List[str]
