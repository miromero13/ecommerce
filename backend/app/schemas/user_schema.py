from pydantic import BaseModel, EmailStr, Field
from typing import List
from uuid import UUID
from app.schemas.enums import RolEnum, GenderEnum

#  Para registro
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    gender: GenderEnum
    branch_id: UUID | None = None


class AdminUserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)
    gender: GenderEnum
    rol: RolEnum
    role_id: UUID | None = None
    tenant_id: UUID | None = None
    branch_id: UUID | None = None
    is_active: bool = True

#  Para login
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    rol: RolEnum | None = None

#  Para leer usuario en respuestas (registro, perfil)
class UserOut(BaseModel):
    id: UUID 
    name: str
    email: EmailStr
    gender: GenderEnum
    rol: RolEnum
    tenant_id: UUID | None = None
    branch_id: UUID | None = None
    is_active: bool
    permissions: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True

class CustomRoleBrief(BaseModel):
    id: UUID
    code: str
    name: str

    model_config = {
        "from_attributes": True
    }


#  Para paginación de usuarios (si aplicas en /users)
class UserRead(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    gender: GenderEnum
    rol: RolEnum
    tenant_id: UUID | None = None
    branch_id: UUID | None = None
    is_active: bool
    permissions: list[str] = Field(default_factory=list)
    custom_roles: list[CustomRoleBrief] = Field(default_factory=list)

    model_config = {
        "from_attributes": True
    }

class UsersPaginatedResponse(BaseModel):
    data: List[UserRead]
    countData: int
    
class UserUpdateRol(BaseModel):
    rol: RolEnum
    tenant_id: UUID | None = None
    branch_id: UUID | None = None


class UserUpdateBranch(BaseModel):
    branch_id: UUID | None = None


class UserUpdate(BaseModel):
    name: str
    email: EmailStr
    gender: GenderEnum
    rol: RolEnum | None = None
    role_id: UUID | None = None
    tenant_id: UUID | None = None
    branch_id: UUID | None = None
    is_active: bool = True


class UserActiveUpdate(BaseModel):
    is_active: bool


class UserProfileUpdate(BaseModel):
    name: str
    email: EmailStr
    gender: GenderEnum
