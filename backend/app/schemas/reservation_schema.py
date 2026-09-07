from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class ReservationStatusEnum(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    attended = "attended"
    cancelled = "cancelled"
    expired = "expired"


class ReservationItemCreate(BaseModel):
    variant_id: UUID
    quantity: int = Field(gt=0)


class ReservationCreate(BaseModel):
    branch_id: UUID
    visit_date: date
    items: list[ReservationItemCreate] = Field(min_length=1)


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
    visit_date: date
    expires_at: date
    status: ReservationStatusEnum
    total_amount: Decimal
    item_count: int
    created_at: datetime
    updated_at: datetime | None = None
    items: list[ReservationItemRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}
