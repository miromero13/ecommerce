from enum import Enum

from pydantic import BaseModel


class CheckoutMethodEnum(str, Enum):
    cash = "cash"
    stripe = "stripe"


class CashPaymentRequest(BaseModel):
    cash_reference: str | None = None


class StripePaymentRequest(BaseModel):
    currency: str | None = None


class StripeCheckoutResponse(BaseModel):
    order_id: str
    client_secret: str
    payment_intent_id: str
