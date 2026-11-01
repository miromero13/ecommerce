from enum import Enum
from datetime import datetime

from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.delivery_schema import DeliveryAddress


class CheckoutMethodEnum(str, Enum):
    cash = "cash"
    stripe = "stripe"


class StripePaymentRequest(BaseModel):
    pickup_branch_id: UUID
    delivery: DeliveryAddress | None = None
    points_to_redeem: int = Field(default=0, ge=0)
    # CU30: when the customer pressed "Comprar" without internet (place in the offline queue).
    offline_requested_at: datetime | None = None


class StripeCheckoutResponse(BaseModel):
    order_id: str
    client_secret: str
    payment_intent_id: str
    pickup_expires_at: str


class CollectCashRequest(BaseModel):
    pickup_code: str


class QrWebhook(BaseModel):
    reference: str
