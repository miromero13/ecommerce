from __future__ import annotations

from decimal import Decimal

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.enums import TenantStatusEnum



HEX_COLOR = r"^#[0-9A-Fa-f]{6}$"  # CU1 branding color, e.g. #1f2937

class TenantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=120, description="Nombre de la marca o e-commerce")
    slug: str = Field(..., min_length=2, max_length=120, description="Identificador único para URLs o catálogos")
    contact_email: EmailStr = Field(..., description="Correo de contacto principal del e-commerce")
    currency: str = Field(default="BOB", max_length=10, description="Moneda por defecto")
    country: Optional[str] = Field(default="Bolivia", max_length=80, description="País de operación")
    status: TenantStatusEnum = Field(default=TenantStatusEnum.active, description="Estado inicial")


class TenantUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    slug: Optional[str] = Field(default=None, min_length=2, max_length=120)
    contact_email: Optional[EmailStr] = None
    currency: Optional[str] = Field(default=None, max_length=10)
    country: Optional[str] = Field(default=None, max_length=80)
    status: Optional[TenantStatusEnum] = None
    platform_fee_percent: Optional[Decimal] = Field(default=None, ge=0, le=100)
    primary_color: Optional[str] = Field(default=None, pattern=HEX_COLOR)


class TenantStatusUpdate(BaseModel):
    status: TenantStatusEnum


class TenantBrandingUpdate(BaseModel):
    primary_color: Optional[str] = Field(default=None, pattern=HEX_COLOR)


class TenantBrandingRead(BaseModel):
    """Public company branding for the staff panel and receipts (CU1)."""
    tenant_id: UUID
    name: str
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    currency: str


class TenantRead(BaseModel):
    id: UUID
    name: str
    slug: str
    contact_email: EmailStr
    currency: str
    country: Optional[str] = None
    status: TenantStatusEnum
    platform_fee_percent: Decimal = Decimal("0")
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    branches_count: int = 0
    users_count: int = 0

    model_config = {
        "from_attributes": True
    }


class TenantPaginatedResponse(BaseModel):
    data: List[TenantRead]
    countData: int
