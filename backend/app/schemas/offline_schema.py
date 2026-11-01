from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class OfflineSaleItemIn(BaseModel):
    variant_id: UUID
    quantity: int = Field(gt=0, le=999)
    unit_price: Decimal = Field(ge=0)  # price charged at the till (already discounted)
    product_name: str | None = Field(default=None, max_length=200)
    variant_sku: str | None = Field(default=None, max_length=80)


class OfflineOperationIn(BaseModel):
    operation_id: str = Field(min_length=1, max_length=64)
    receipt_number: str = Field(min_length=1, max_length=40)
    type: str = "cash_sale"
    created_at: datetime | None = None
    branch_id: UUID
    cashier_id: UUID | None = None
    cash_session_id: UUID | None = None
    customer_name: str | None = Field(default=None, max_length=120)
    customer_phone: str | None = Field(default=None, max_length=40)
    customer_email: str | None = Field(default=None, max_length=255)
    items: list[OfflineSaleItemIn] = Field(min_length=1, max_length=100)
    subtotal: Decimal = Field(ge=0)
    discount: Decimal = Field(default=Decimal("0"), ge=0)
    total: Decimal = Field(ge=0)
    cash_received: Decimal | None = Field(default=None, ge=0)
    change_returned: Decimal | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=500)


class OfflineQueueSyncRequest(BaseModel):
    operations: list[OfflineOperationIn] = Field(max_length=200)


class ExchangeItemIn(BaseModel):
    variant_id: UUID
    quantity: int = Field(gt=0, le=999)


class ConflictResolveRequest(BaseModel):
    action: Literal["cash_refund", "wallet_credit", "exchange", "delivered"]
    customer_email: str | None = Field(default=None, max_length=255)  # wallet credit (whole or difference)
    exchange_items: list[ExchangeItemIn] | None = Field(default=None, max_length=50)
    difference_method: Literal["cash", "wallet"] = "cash"  # exchange for a cheaper garment
    cash_received: Decimal | None = Field(default=None, ge=0)  # exchange for a pricier garment
    notes: str | None = Field(default=None, max_length=500)
