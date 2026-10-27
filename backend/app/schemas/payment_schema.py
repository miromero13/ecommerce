from enum import Enum

from uuid import UUID

from pydantic import BaseModel

from app.schemas.delivery_schema import DeliveryAddress


class CheckoutMethodEnum(str, Enum):
    cash = "cash"
    stripe = "stripe"


class CashPaymentRequest(BaseModel):
    pickup_branch_id: UUID
    delivery: DeliveryAddress | None = None  # CU20: ship from pickup_branch_id instead of in-store pickup


class StripePaymentRequest(BaseModel):
    pickup_branch_id: UUID
    delivery: DeliveryAddress | None = None


class StripeCheckoutResponse(BaseModel):
    order_id: str
    client_secret: str
    payment_intent_id: str
    pickup_expires_at: str


class CollectCashRequest(BaseModel):
    pickup_code: str
