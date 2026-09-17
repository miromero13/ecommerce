from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class CartStatusEnum(str, Enum):
    active = "active"
    checkout_pending = "checkout_pending"
    checked_out = "checked_out"
    cancelled = "cancelled"


class CartItemCreate(BaseModel):
    variant_id: UUID
    branch_id: UUID | None = None
    reservation_id: UUID | None = None
    quantity: int = Field(gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=0)


class CartItemRead(BaseModel):
    id: UUID
    cart_id: UUID
    variant_id: UUID
    quantity: int
    unit_price: Decimal
    original_unit_price: Decimal | None = None
    discount_amount: Decimal = Decimal("0.00")
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


class CartRead(BaseModel):
    id: UUID
    user_id: UUID
    status: CartStatusEnum
    subtotal: Decimal
    discount_amount: Decimal
    promotion_code_id: UUID | None = None
    promotion_code: str | None = None
    total_amount: Decimal
    item_count: int
    created_at: datetime
    updated_at: datetime | None = None
    items: list[CartItemRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}
