from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class GiftCardPurchaseRequest(BaseModel):
    amount: Decimal = Field(..., ge=Decimal("10.00"), description="Monto en dinero de la tarjeta de regalo (mínimo 10.00)")
    recipient_name: str = Field(..., min_length=2, max_length=120)
    recipient_email: EmailStr
    custom_message: str | None = Field(default=None, max_length=500)
    payment_method: str = Field(default="stripe", description="stripe, card o wallet")
    tenant_id: UUID | None = Field(default=None, description="Opcional: empresa emisora de la tarjeta")


class GiftCardResponse(BaseModel):
    id: UUID
    code: str
    amount: Decimal
    balance: Decimal
    recipient_name: str
    recipient_email: str
    custom_message: str | None = None
    status: str
    qr_code_url: str | None = None
    expires_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class GiftCardVerifyResponse(BaseModel):
    code: str
    amount: Decimal
    balance: Decimal
    status: str
    recipient_name: str
    expires_at: datetime | None = None
