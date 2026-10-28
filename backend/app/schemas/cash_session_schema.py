from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class CashSessionOpen(BaseModel):
    opening_amount: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2)


class CashMovementCreate(BaseModel):
    type: Literal["deposit", "withdrawal"]
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    reason: str = Field(..., min_length=3, max_length=255)


class CashSessionClose(BaseModel):
    counted_amount: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2)
    note: str | None = Field(default=None, max_length=255)
