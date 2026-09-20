from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from decimal import Decimal
from enum import Enum

from app.schemas.catalog_enums import ProductStatusEnum


class NameCreate(BaseModel):
    name: str


class ColorCreate(BaseModel):
    name: str
    hex_code: str | None = None


class CollectionCreate(BaseModel):
    name: str
    season_id: UUID | None = None


class DiscountTypeEnum(str, Enum):
    percentage = "percentage"
    fixed = "fixed"


class Point(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class ProductVariantCreate(BaseModel):
    id: UUID | None = None
    sku: str
    price: Decimal
    size_id: UUID | None = None
    color_id: UUID | None = None
    image_url: str | None = None
    image_public_id: str | None = None
    status: ProductStatusEnum | None = None


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    category_id: UUID
    collection_id: UUID | None = None
    discount_type: DiscountTypeEnum | None = None
    discount_value: Decimal | None = Field(default=None, ge=0)
    provider_id: UUID | None = None
    status: ProductStatusEnum | None = None
    variants: list[ProductVariantCreate] = Field(min_length=1)


class ProductVariantStatusUpdate(BaseModel):
    status: ProductStatusEnum


class ProductVariantGarmentPointsUpdate(BaseModel):
    garment_points: list[Point] | None

    @field_validator("garment_points")
    @classmethod
    def validate_point_count(cls, points: list[Point] | None) -> list[Point] | None:
        if points is not None and len(points) not in (17, 19):
            raise ValueError("garment_points must contain exactly 17 or 19 points")
        return points


class ProductVariantRead(BaseModel):
    id: UUID
    product_id: UUID
    sku: str
    price: Decimal
    original_price: Decimal | None = None
    discount_amount: Decimal = Decimal("0.00")
    size_id: UUID | None = None
    color_id: UUID | None = None
    image_url: str | None = None
    image_public_id: str | None = None
    garment_points: list[Point] | None = None
    status: ProductStatusEnum
    branch_quantity: int | None = None
    provider_quantity: int | None = None

    model_config = {
        "from_attributes": True,
    }


class ProductRead(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    discount_type: DiscountTypeEnum | None = None
    discount_value: Decimal | None = None
    provider_id: UUID | None = None
    category_id: UUID
    collection_id: UUID | None = None
    sku: str | None = None
    image_url: str | None = None
    image_public_id: str | None = None
    status: ProductStatusEnum | None = None
    size_id: UUID | None = None
    color_id: UUID | None = None
    branch_quantity: int | None = None
    variants: list[ProductVariantRead] = Field(default_factory=list)

    model_config = {
        "from_attributes": True,
    }
