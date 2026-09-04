from pydantic import BaseModel, EmailStr
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

#  Para login
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    rol: RolEnum

#  Para leer usuario en respuestas (registro, perfil)
class UserOut(BaseModel):
    id: UUID 
    name: str
    email: EmailStr
    gender: GenderEnum
    rol: RolEnum
    branch_id: UUID | None = None
    is_active: bool


    class Config:
        from_attributes = True

#  Para paginación de usuarios (si aplicas en /users)
class UserRead(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    gender: GenderEnum
    rol: RolEnum
    branch_id: UUID | None = None
    is_active: bool

    model_config = {
        "from_attributes": True
    }

class UsersPaginatedResponse(BaseModel):
    data: List[UserRead]
    countData: int
    
class UserUpdateRol(BaseModel):
    rol: RolEnum


class UserUpdateBranch(BaseModel):
    branch_id: UUID | None = None


class UserUpdate(BaseModel):
    name: str
    email: EmailStr
    password: str | None = None
    gender: GenderEnum
    branch_id: UUID | None = None
    is_active: bool = True


class UserActiveUpdate(BaseModel):
    is_active: bool
