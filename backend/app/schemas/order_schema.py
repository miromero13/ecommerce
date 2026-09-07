from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class OrderStatusEnum(str, Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    cancelled = "cancelled"


class PaymentMethodEnum(str, Enum):
    cash = "cash"
    stripe = "stripe"


class PaymentStatusEnum(str, Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"


class CashCheckoutCreate(BaseModel):
    cash_reference: str | None = None


class StripeCheckoutCreate(BaseModel):
    currency: str | None = None


class OrderItemRead(BaseModel):
    id: UUID
    order_id: UUID
    variant_id: UUID
    quantity: int
    unit_price: Decimal
    line_total: Decimal
    product_id: UUID
    product_name: str
    variant_sku: str
    size_id: UUID | None = None
    color_id: UUID | None = None
    size_name: str | None = None
    color_name: str | None = None
    image_url: str | None = None
    image_public_id: str | None = None

    model_config = {"from_attributes": True}


class OrderRead(BaseModel):
    id: UUID
    user_id: UUID
    status: OrderStatusEnum
    payment_method: PaymentMethodEnum
    payment_status: PaymentStatusEnum
    stripe_payment_intent_id: str | None = None
    cash_reference: str | None = None
    subtotal: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime | None = None
    items: list[OrderItemRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}
