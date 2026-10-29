from uuid import UUID
from pydantic import BaseModel, Field

from app.schemas.enums import RolEnum


class PermissionRead(BaseModel):
    id: UUID
    name: str
    module: str
    description: str

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=64)
    permission_ids: list[UUID] = Field(min_length=1)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    permission_ids: list[UUID] | None = None


class RoleRead(BaseModel):
    id: UUID
    tenant_id: UUID | None = None
    code: str
    name: str
    base_rol: RolEnum | None = None
    is_system: bool = False
    permissions: list[PermissionRead] = []

    model_config = {"from_attributes": True}


class UserRolesAssign(BaseModel):
    role_ids: list[UUID] = Field(default_factory=list)
