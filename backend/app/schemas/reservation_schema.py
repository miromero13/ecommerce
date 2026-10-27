from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ReservationStatusEnum(str, Enum):
    pending_payment = "pending_payment"
    pending = "pending"
    confirmed = "confirmed"
    attended = "attended"
    purchase_pending = "purchase_pending"
    sold = "sold"
    not_sold = "not_sold"
    cancelled = "cancelled"
    expired = "expired"


class ReservationItemCreate(BaseModel):
    variant_id: UUID
    quantity: int = Field(gt=0)


class ReservationCreate(BaseModel):
    branch_id: UUID
    visit_date: date
    items: list[ReservationItemCreate] = Field(min_length=1)

    @field_validator("visit_date", mode="before")
    @classmethod
    def parse_visit_date(cls, v):
        if isinstance(v, str):
            if "T" in v:
                v = v.split("T")[0]
            elif " " in v:
                v = v.split(" ")[0]
            return date.fromisoformat(v)
        if isinstance(v, datetime):
            return v.date()
        return v


class ReservationDecisionRequest(BaseModel):
    purchase: bool


class ReservationItemRead(BaseModel):
    id: UUID
    reservation_id: UUID
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


class ReservationRead(BaseModel):
    id: UUID
    branch_id: UUID
    branch_name: str
    user_id: UUID
    user_name: str
    cart_id: UUID | None = None
    visit_date: date
    expires_at: date
    status: ReservationStatusEnum
    total_amount: Decimal
    deposit_amount: Decimal = Decimal("0")
    deposit_status: str = "none"
    payment_expires_at: datetime | None = None
    item_count: int
    created_at: datetime
    updated_at: datetime | None = None
    items: list[ReservationItemRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}
