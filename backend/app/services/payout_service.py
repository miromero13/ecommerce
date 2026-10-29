"""Platform collection model: online payments (card, QR) land in the platform
account, are recorded per company in payment_transactions and paid out to the
company's bank account in one settlement per day. Cash never passes through here."""
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.payout import PaymentTransaction, Settlement
from app.models.tenant import Tenant

CENT = Decimal("0.01")
BANK_FIELDS = ("bank_name", "bank_account_number", "bank_account_holder")


def record_payment(db: Session, tenant_id: UUID, source_type: str, source_id: UUID, method: str,
                   amount, currency: str, provider_reference: str | None = None) -> PaymentTransaction:
    """Idempotent per (source_type, source_id): a retried webhook never double-counts."""
    existing = db.query(PaymentTransaction).filter_by(source_type=source_type, source_id=source_id).first()
    if existing:
        return existing
    fee_percent = db.query(Tenant.platform_fee_percent).filter(Tenant.id == tenant_id).scalar() or 0
    gross = Decimal(str(amount)).quantize(CENT)
    fee = (gross * Decimal(str(fee_percent)) / 100).quantize(CENT, rounding=ROUND_HALF_UP)
    transaction = PaymentTransaction(
        tenant_id=tenant_id, source_type=source_type, source_id=source_id, method=method,
        gross_amount=gross, fee_amount=fee, net_amount=gross - fee, currency=currency,
        provider_reference=provider_reference,
    )
    db.add(transaction)
    db.flush()
    return transaction


def run_daily_settlements(db: Session, today: date | None = None) -> list[Settlement]:
    """Settle every unsettled payment made before today, one settlement per company per day."""
    today = today or date.today()
    cutoff = datetime.combine(today, time.min).astimezone(timezone.utc)
    pending = (db.query(PaymentTransaction)
               .filter(PaymentTransaction.settlement_id.is_(None), PaymentTransaction.created_at < cutoff)
               .with_for_update(skip_locked=True).all())
    by_tenant: dict[UUID, list[PaymentTransaction]] = defaultdict(list)
    for transaction in pending:
        by_tenant[transaction.tenant_id].append(transaction)

    created = []
    period = today - timedelta(days=1)
    for tenant_id, transactions in by_tenant.items():
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).one()
        settlement = Settlement(
            tenant_id=tenant_id, period_date=period, currency=transactions[0].currency,
            gross_amount=sum((t.gross_amount for t in transactions), Decimal("0")),
            fee_amount=sum((t.fee_amount for t in transactions), Decimal("0")),
            net_amount=sum((t.net_amount for t in transactions), Decimal("0")),
            transactions_count=len(transactions),
            **{field: getattr(tenant, field) for field in BANK_FIELDS},
        )
        db.add(settlement)
        db.flush()
        for transaction in transactions:
            transaction.settlement_id = settlement.id
        created.append(settlement)
    db.commit()
    return created


def list_settlements(db: Session, tenant_id: UUID | None = None) -> list[Settlement]:
    query = db.query(Settlement)
    if tenant_id is not None:
        query = query.filter(Settlement.tenant_id == tenant_id)
    return query.order_by(Settlement.period_date.desc(), Settlement.created_at.desc()).all()


def mark_settlement_paid(db: Session, settlement_id: UUID, transfer_reference: str, paid_by: UUID) -> Settlement:
    settlement = db.query(Settlement).filter(Settlement.id == settlement_id).with_for_update().first()
    if not settlement:
        raise LookupError("Liquidación no encontrada")
    if settlement.status == "paid":
        raise RuntimeError("La liquidación ya fue transferida")
    if not settlement.bank_account_number:
        # The company may register its account after the settlement was issued.
        tenant = db.query(Tenant).filter(Tenant.id == settlement.tenant_id).one()
        for field in BANK_FIELDS:
            setattr(settlement, field, getattr(tenant, field))
    if not settlement.bank_account_number:
        raise ValueError("La empresa no registró su cuenta bancaria")
    settlement.status = "paid"
    settlement.transfer_reference = transfer_reference
    settlement.paid_at = datetime.now(timezone.utc)
    settlement.paid_by = paid_by
    db.commit()
    db.refresh(settlement)
    return settlement


def update_bank_account(db: Session, tenant_id: UUID, data: dict) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).one()
    for field in BANK_FIELDS:
        setattr(tenant, field, data[field])
    db.commit()
    db.refresh(tenant)
    return tenant


def get_summary(db: Session, tenant_id: UUID) -> dict:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).one()
    unsettled = db.query(func.coalesce(func.sum(PaymentTransaction.net_amount), 0)).filter(
        PaymentTransaction.tenant_id == tenant_id, PaymentTransaction.settlement_id.is_(None)).scalar()
    awaiting_transfer = db.query(func.coalesce(func.sum(Settlement.net_amount), 0)).filter(
        Settlement.tenant_id == tenant_id, Settlement.status == "pending").scalar()
    transferred = db.query(func.coalesce(func.sum(Settlement.net_amount), 0)).filter(
        Settlement.tenant_id == tenant_id, Settlement.status == "paid").scalar()
    recent = (db.query(PaymentTransaction).filter(PaymentTransaction.tenant_id == tenant_id)
              .order_by(PaymentTransaction.created_at.desc()).limit(20).all())
    return {
        "currency": tenant.currency,
        "platform_fee_percent": tenant.platform_fee_percent,
        "pending_net_amount": Decimal(unsettled) + Decimal(awaiting_transfer),
        "transferred_net_amount": Decimal(transferred),
        "bank_account": {field: getattr(tenant, field) for field in BANK_FIELDS},
        "recent_transactions": recent,
    }
