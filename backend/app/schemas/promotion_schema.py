from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class PromotionDiscountType(str, Enum):
    percentage = "percentage"
    fixed = "fixed"


class PromotionCodeCreate(BaseModel):
    code: str = Field(min_length=3, max_length=40)
    discount_type: PromotionDiscountType
    discount_value: Decimal = Field(gt=0)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    branch_id: UUID | None = None
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @model_validator(mode="after")
    def validate_discount(self):
        if self.discount_type == PromotionDiscountType.percentage and self.discount_value > 100:
            raise ValueError("El descuento porcentual no puede superar el 100%")
        if self.valid_from and self.valid_until and self.valid_until <= self.valid_from:
            raise ValueError("La fecha de finalización debe ser posterior al inicio")
        if self.valid_from and self.valid_from.tzinfo is None:
            self.valid_from = self.valid_from.replace(tzinfo=timezone.utc)
        if self.valid_until and self.valid_until.tzinfo is None:
            self.valid_until = self.valid_until.replace(tzinfo=timezone.utc)
        return self


class PromotionCodeRead(BaseModel):
    id: UUID
    code: str
    discount_type: PromotionDiscountType
    discount_value: Decimal
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    branch_id: UUID | None = None
    created_by: UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PromotionCodeApply(BaseModel):
    code: str = Field(min_length=1, max_length=40)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()
