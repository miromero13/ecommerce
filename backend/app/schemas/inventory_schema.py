from enum import Enum
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class InventoryMovementTypeEnum(str, Enum):
    income = "income"
    outcome = "outcome"
    transfer_in = "transfer_in"
    transfer_out = "transfer_out"


class InventoryMovementCreate(BaseModel):
    variant_id: UUID
    branch_id: UUID
    quantity: int = Field(gt=0)
    note: str | None = None


class InventoryTransferCreate(BaseModel):
    variant_id: UUID
    from_branch_id: UUID
    to_branch_id: UUID
    quantity: int = Field(gt=0)
    note: str | None = None


class InventoryMovementRead(BaseModel):
    id: UUID
    variant_id: UUID
    branch_id: UUID
    movement_type: InventoryMovementTypeEnum
    quantity: int
    reference_branch_id: UUID | None = None
    note: str | None = None
    created_by: UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
