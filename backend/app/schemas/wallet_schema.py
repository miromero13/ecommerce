from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class WalletBalanceResponse(BaseModel):
    balance: Decimal
    currency: str = "BOB"


class WalletRedeemRequest(BaseModel):
    card_code: str = Field(..., min_length=4, max_length=32)


class WalletRedeemResponse(BaseModel):
    credited_amount: Decimal
    new_balance: Decimal


class WalletPayRequest(BaseModel):
    order_id: UUID
    amount_to_debit: Decimal = Field(..., gt=Decimal("0.00"))


class WalletCheckoutRequest(BaseModel):
    pickup_branch_id: UUID
    delivery: dict | None = None
    points_to_redeem: int = 0


class WalletConvertPointsRequest(BaseModel):
    tenant_id: UUID
    points: int = Field(..., gt=0, description="Puntos a convertir en múltiplos de 100")


class WalletConvertPointsResponse(BaseModel):
    converted_points: int
    credited_amount: Decimal
    new_balance: Decimal
    tenant_name: str


class WalletTransactionResponse(BaseModel):
    id: UUID
    type: str  # credit | debit
    amount: Decimal
    balance_after: Decimal
    concept: str
    source_type: str | None = None
    source_id: UUID | None = None
    description: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
