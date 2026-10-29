from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import EmailStr, BaseModel, Field, model_validator

from app.schemas.order_schema import PaymentMethodEnum, PaymentStatusEnum


class SaleStatusEnum(str, Enum):
    completed = "completed"
    cancelled = "cancelled"


class SaleTypeEnum(str, Enum):
    in_person = "venta presencial"
    online = "venta virtual"


class SaleItemCreate(BaseModel):
    variant_id: UUID
    quantity: int = Field(gt=0)


class SaleCreate(BaseModel):
    branch_id: UUID | None = None
    reservation_id: UUID | None = None
    payment_method: PaymentMethodEnum = PaymentMethodEnum.cash
    cash_reference: str | None = None
    qr_reference: str | None = None  # required when payment_method is "qr"
    promotion_code: str | None = Field(default=None, max_length=40)
    customer_email: EmailStr | None = None  # registered customer; required with a coupon or points
    points_to_redeem: int = Field(default=0, ge=0)  # CU17: 10 points = 1 Bs
    # 1P-CU18 cash drawer: cash handed over by the customer; omitted means the exact amount (no change).
    cash_received: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    items: list[SaleItemCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_items_or_reservation(self):
        if self.reservation_id:
            raise ValueError("CU18 no permite ventas asociadas a reservas")
        if self.payment_method not in (PaymentMethodEnum.cash, PaymentMethodEnum.qr):
            raise ValueError("Las ventas directas aceptan efectivo o QR")
        if not self.items:
            raise ValueError("La venta no tiene items")
        return self


class SaleItemRead(BaseModel):
    id: UUID
    sale_id: UUID
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


class SaleRead(BaseModel):
    id: UUID
    branch_id: UUID
    branch_name: str
    type: SaleTypeEnum
    user_id: UUID
    reservation_id: UUID | None = None
    status: SaleStatusEnum
    payment_method: PaymentMethodEnum
    payment_status: PaymentStatusEnum
    cash_reference: str | None = None
    customer_id: UUID | None = None
    promotion_code_id: UUID | None = None
    subtotal: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime | None = None
    items: list[SaleItemRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}
