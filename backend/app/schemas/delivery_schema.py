from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.enums import GenderEnum


class Coordinates(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class DeliveryQuoteRequest(Coordinates):
    branch_id: UUID


class DeliveryAddress(Coordinates):
    address: str = Field(min_length=5, max_length=255)
    reference: str | None = Field(default=None, max_length=255)


class ConfirmDeliveryRequest(BaseModel):
    order_id: UUID
    security_pin: str = Field(pattern=r"^\d{4}$")


class DriverCreate(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr
    password: str = Field(min_length=8)
    gender: GenderEnum
