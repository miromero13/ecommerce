from pydantic import BaseModel, Field
from uuid import UUID


class BranchCreate(BaseModel):
    name: str
    city: str
    is_default: bool = False
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class BranchRead(BaseModel):
    id: UUID
    tenant_id: UUID | None = None
    name: str
    city: str
    is_default: bool
    is_active: bool
    latitude: float | None = None
    longitude: float | None = None

    model_config = {
        "from_attributes": True,
    }


class BranchUpdate(BaseModel):
    name: str
    city: str
    is_default: bool = False
    is_active: bool = True
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class BranchActiveUpdate(BaseModel):
    is_active: bool
