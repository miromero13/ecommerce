from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal

from app.schemas.catalog_enums import ProductStatusEnum


class NameCreate(BaseModel):
    name: str


class ColorCreate(BaseModel):
    name: str
    hex_code: str | None = None


class CollectionCreate(BaseModel):
    name: str
    season_id: UUID | None = None


class ProductCreate(BaseModel):
    sku: str
    name: str
    description: str | None = None
    price: Decimal
    category_id: UUID
    size_id: UUID | None = None
    color_id: UUID | None = None
    season_id: UUID | None = None
    collection_id: UUID | None = None


class ProductStatusUpdate(BaseModel):
    status: ProductStatusEnum


class ProductRead(BaseModel):
    id: UUID
    sku: str
    name: str
    description: str | None = None
    price: Decimal
    status: ProductStatusEnum
    category_id: UUID
    size_id: UUID | None = None
    color_id: UUID | None = None
    season_id: UUID | None = None
    collection_id: UUID | None = None
    branch_quantity: int | None = None

    model_config = {
        "from_attributes": True,
    }
