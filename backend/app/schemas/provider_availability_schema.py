from uuid import UUID

from pydantic import BaseModel, Field


class ProviderAvailabilityUpdate(BaseModel):
    variant_id: UUID
    quantity: int = Field(ge=0)


class ProviderAvailabilityBatchUpdate(BaseModel):
    updates: list[ProviderAvailabilityUpdate]
