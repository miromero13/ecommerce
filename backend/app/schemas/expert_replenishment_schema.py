from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExpertRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    lookback_days: int
    coverage_days: int
    is_auto_enabled: bool
    created_at: datetime
    updated_at: datetime


class ExpertRuleUpdate(BaseModel):
    lookback_days: int | None = Field(default=None, ge=1, le=90)
    coverage_days: int | None = Field(default=None, ge=1, le=90)
    is_auto_enabled: bool | None = None


class ExpertSuggestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    variant_id: UUID
    source_branch_id: UUID
    target_branch_id: UUID
    suggested_quantity: int
    reason: str
    status: str
    created_at: datetime
    applied_at: datetime | None = None
    product_name: str | None = None
    variant_sku: str | None = None
    source_branch_name: str | None = None
    target_branch_name: str | None = None


class ApplyTransfersRequest(BaseModel):
    transfer_ids: list[UUID] = Field(..., min_length=1)
