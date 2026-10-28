from uuid import UUID

from pydantic import BaseModel, Field


class WishlistItemCreate(BaseModel):
    product_id: UUID


class MoveToCartRequest(BaseModel):
    variant_id: UUID  # the size/color chosen when moving the favorite to the cart
    branch_id: UUID | None = None
    quantity: int = Field(default=1, gt=0, le=20)
