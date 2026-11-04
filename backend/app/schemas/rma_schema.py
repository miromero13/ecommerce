"""CU21 & CU24: Schemas for RMA requests, items, inspection reviews, and eligible orders."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RmaItemCreate(BaseModel):
    order_item_id: UUID
    quantity: int = Field(default=1, ge=1)
    reason: str  # wrong_size | wrong_color | factory_defect | change_of_mind
    preferred_resolution: str  # exchange | store_credit
    requested_variant_id: UUID | None = None
    customer_notes: str | None = None


class RmaRequestCreate(BaseModel):
    order_id: UUID
    customer_notes: str | None = None
    items: list[RmaItemCreate] = Field(min_length=1)


class RmaItemReview(BaseModel):
    status: str  # approved | rejected
    item_condition: str  # intact | factory_damaged | customer_damaged
    action: str  # restock_available | scrap_quarantine | return_to_customer
    resolution: str = "store_credit"  # exchange | store_credit
    replacement_variant_id: UUID | None = None
    branch_id: UUID | None = None
    inspection_notes: str | None = None


class SameProductVariant(BaseModel):
    variant_id: UUID
    sku: str
    size_name: str | None = None
    color_name: str | None = None
    stock: int = 0


class EligibleOrderItemRead(BaseModel):
    order_item_id: UUID
    product_id: UUID
    product_name: str
    variant_id: UUID
    sku: str
    size_name: str | None = None
    color_name: str | None = None
    unit_price: float
    quantity: int
    image_url: str | None = None
    eligible_for_rma: bool
    ineligible_reason: str | None = None
    same_product_variants: list[SameProductVariant] = []


class EligibleOrderRead(BaseModel):
    order_id: UUID
    order_number: str
    delivered_at: datetime | None = None
    created_at: datetime
    days_since_delivery: int
    items: list[EligibleOrderItemRead]


class RmaItemRead(BaseModel):
    id: UUID
    order_item_id: UUID
    product_name: str
    original_sku: str
    original_size: str | None = None
    original_color: str | None = None
    unit_price: float
    quantity: int
    image_url: str | None = None
    reason: str
    preferred_resolution: str
    requested_variant_id: UUID | None = None
    requested_variant_label: str | None = None
    customer_notes: str | None = None
    item_condition: str | None = None
    action: str | None = None
    status: str
    replacement_variant_id: UUID | None = None
    replacement_variant_label: str | None = None
    branch_id: UUID | None = None
    branch_name: str | None = None
    inspection_notes: str | None = None
    quarantine_record: str | None = None
    refund_amount: float | None = None
    wallet_settlement_date: datetime | None = None
    settlement_status: str | None = None


class RmaRequestRead(BaseModel):
    id: UUID
    tenant_id: UUID
    order_id: UUID
    order_number: str
    user_id: UUID
    customer_name: str
    customer_email: str
    rma_number: str
    status: str
    customer_notes: str | None = None
    pdf_url: str
    created_at: datetime
    updated_at: datetime | None = None
    items: list[RmaItemRead]
