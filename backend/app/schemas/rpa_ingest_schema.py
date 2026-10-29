from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ExtractedItem(BaseModel):
    """One garment line read from a supplier document (also Gemini's response schema)."""
    sku: str = Field(min_length=1, max_length=80)
    name: str = Field(default="", max_length=200)
    size: str | None = Field(default=None, max_length=40)
    color: str | None = Field(default=None, max_length=40)
    quantity: int = Field(gt=0, le=100000)
    unit_cost: Decimal | None = Field(default=None, ge=0)


class ItemsCorrection(BaseModel):
    items: list[ExtractedItem] = Field(min_length=1, max_length=500)


class JobCommit(BaseModel):
    branch_id: UUID


class RpaJobRead(BaseModel):
    job_id: UUID
    filename: str
    status: str
    extracted_items: list[dict]
    error_message: str | None = None
    target_branch_id: UUID | None = None
    committed_at: datetime | None = None
    created_at: datetime
