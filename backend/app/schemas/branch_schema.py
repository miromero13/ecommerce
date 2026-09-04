from pydantic import BaseModel
from uuid import UUID


class BranchRead(BaseModel):
    id: UUID
    name: str
    city: str
    is_default: bool

    model_config = {
        "from_attributes": True,
    }
