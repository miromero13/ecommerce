from enum import Enum

from uuid import UUID

from pydantic import BaseModel


class CheckoutMethodEnum(str, Enum):
    cash = "cash"
    stripe = "stripe"


class CashPaymentRequest(BaseModel):
    pickup_branch_id: UUID


class StripePaymentRequest(BaseModel):
    pickup_branch_id: UUID


class StripeCheckoutResponse(BaseModel):
    order_id: str
    client_secret: str
    payment_intent_id: str
    pickup_expires_at: str


class CollectCashRequest(BaseModel):
    pickup_code: str
