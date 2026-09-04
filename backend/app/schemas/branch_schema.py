from pydantic import BaseModel
from uuid import UUID


class BranchCreate(BaseModel):
    name: str
    city: str
    is_default: bool = False


class BranchRead(BaseModel):
    id: UUID
    name: str
    city: str
    is_default: bool
    is_active: bool

    model_config = {
        "from_attributes": True,
    }


class BranchUpdate(BaseModel):
    name: str
    city: str
    is_default: bool = False
    is_active: bool = True
