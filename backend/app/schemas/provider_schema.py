from pydantic import BaseModel, EmailStr
from uuid import UUID

from app.schemas.enums import ProviderStatusEnum, GenderEnum


class ProviderCreate(BaseModel):
    business_name: str
    contact_name: str
    email: EmailStr
    password: str
    gender: GenderEnum
    phone: str | None = None
    branch_id: UUID | None = None


class ProviderStatusUpdate(BaseModel):
    status: ProviderStatusEnum


class ProviderRead(BaseModel):
    id: UUID
    user_id: UUID
    business_name: str
    contact_name: str
    email: EmailStr
    gender: GenderEnum
    phone: str | None = None
    branch_id: UUID | None = None
    status: ProviderStatusEnum
    is_active: bool


class ProviderUpdate(BaseModel):
    business_name: str
    contact_name: str
    email: EmailStr
    password: str | None = None
    gender: GenderEnum
    phone: str | None = None
    branch_id: UUID | None = None
    status: ProviderStatusEnum = ProviderStatusEnum.active
    is_active: bool = True


class ProviderActiveUpdate(BaseModel):
    is_active: bool
