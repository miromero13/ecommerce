from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class BankAccountUpdate(BaseModel):
    bank_name: str = Field(min_length=2, max_length=120)
    bank_account_number: str = Field(min_length=5, max_length=40, pattern=r"^[0-9-]+$")
    bank_account_holder: str = Field(min_length=2, max_length=160)


class TransferConfirm(BaseModel):
    transfer_reference: str = Field(min_length=3, max_length=120)


class SettlementRead(BaseModel):
    id: UUID
    tenant_id: UUID
    tenant_name: str | None = None
    period_date: date
    gross_amount: Decimal
    fee_amount: Decimal
    net_amount: Decimal
    transactions_count: int
    currency: str
    status: str
    bank_name: str | None = None
    bank_account_number: str | None = None
    bank_account_holder: str | None = None
    transfer_reference: str | None = None
    paid_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentTransactionRead(BaseModel):
    id: UUID
    source_type: str
    source_id: UUID
    method: str
    gross_amount: Decimal
    fee_amount: Decimal
    net_amount: Decimal
    currency: str
    settlement_id: UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PayoutSummaryRead(BaseModel):
    currency: str
    platform_fee_percent: Decimal
    pending_net_amount: Decimal
    transferred_net_amount: Decimal
    bank_account: dict
    recent_transactions: list[PaymentTransactionRead]
