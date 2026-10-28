from decimal import Decimal
from enum import Enum

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.delivery_schema import DeliveryAddress


class CheckoutMethodEnum(str, Enum):
    cash = "cash"
    stripe = "stripe"


class CashPaymentRequest(BaseModel):
    pickup_branch_id: UUID
    delivery: DeliveryAddress | None = None  # CU20: ship from pickup_branch_id instead of in-store pickup
    points_to_redeem: int = Field(default=0, ge=0)  # CU17: 10 points = 1 Bs off the products


class StripePaymentRequest(BaseModel):
    pickup_branch_id: UUID
    delivery: DeliveryAddress | None = None
    points_to_redeem: int = Field(default=0, ge=0)


class StripeCheckoutResponse(BaseModel):
    order_id: str
    client_secret: str
    payment_intent_id: str
    pickup_expires_at: str


class CollectCashRequest(BaseModel):
    pickup_code: str
    # 1P-CU18: cash handed over when a cash order is charged at the counter; omitted means the exact amount.
    cash_received: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)


class QrWebhook(BaseModel):
    reference: str
