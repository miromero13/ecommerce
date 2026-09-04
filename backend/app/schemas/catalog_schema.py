from pydantic import BaseModel, Field
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


class ProductVariantCreate(BaseModel):
    sku: str
    price: Decimal | None = None
    size_id: UUID | None = None
    color_id: UUID | None = None
    status: ProductStatusEnum | None = None


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: Decimal
    category_id: UUID
    season_id: UUID | None = None
    collection_id: UUID | None = None
    provider_id: UUID | None = None
    sku: str | None = None
    size_id: UUID | None = None
    color_id: UUID | None = None
    status: ProductStatusEnum | None = None
    variants: list[ProductVariantCreate] | None = None


class ProductVariantStatusUpdate(BaseModel):
    status: ProductStatusEnum


class ProductVariantRead(BaseModel):
    id: UUID
    product_id: UUID
    sku: str
    price: Decimal
    size_id: UUID | None = None
    color_id: UUID | None = None
    status: ProductStatusEnum
    branch_quantity: int | None = None

    model_config = {
        "from_attributes": True,
    }


class ProductRead(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    price: Decimal
    provider_id: UUID | None = None
    category_id: UUID
    season_id: UUID | None = None
    collection_id: UUID | None = None
    sku: str | None = None
    price: Decimal | None = None
    status: ProductStatusEnum | None = None
    size_id: UUID | None = None
    color_id: UUID | None = None
    branch_quantity: int | None = None
    variants: list[ProductVariantRead] = Field(default_factory=list)

    model_config = {
        "from_attributes": True,
    }
