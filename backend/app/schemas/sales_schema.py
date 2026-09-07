from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.order_schema import PaymentMethodEnum, PaymentStatusEnum


class SaleStatusEnum(str, Enum):
    completed = "completed"
    cancelled = "cancelled"


class SaleItemCreate(BaseModel):
    variant_id: UUID
    quantity: int = Field(gt=0)


class SaleCreate(BaseModel):
    branch_id: UUID | None = None
    reservation_id: UUID | None = None
    payment_method: PaymentMethodEnum = PaymentMethodEnum.cash
    cash_reference: str | None = None
    items: list[SaleItemCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_items_or_reservation(self):
        if not self.reservation_id and not self.items:
            raise ValueError("Debes enviar items o una reserva asociada")
        return self


class SaleItemRead(BaseModel):
    id: UUID
    sale_id: UUID
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


class SaleRead(BaseModel):
    id: UUID
    branch_id: UUID
    branch_name: str
    user_id: UUID
    reservation_id: UUID | None = None
    status: SaleStatusEnum
    payment_method: PaymentMethodEnum
    payment_status: PaymentStatusEnum
    cash_reference: str | None = None
    subtotal: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime | None = None
    items: list[SaleItemRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}
