from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field

class ReplenishmentStatusEnum(str, Enum):
    requested = "requested"
    accepted = "accepted"
    preparing = "preparing"
    awaiting_receipt = "awaiting_receipt"
    delivered = "delivered"

class ReplenishmentItemCreate(BaseModel):
    variant_id: UUID
    requested_quantity: int = Field(gt=0)

class ReplenishmentRequestCreate(BaseModel):
    provider_id: UUID
    branch_id: UUID
    items: list[ReplenishmentItemCreate] = Field(min_length=1)

class ReplenishmentStatusUpdate(BaseModel):
    status: ReplenishmentStatusEnum
