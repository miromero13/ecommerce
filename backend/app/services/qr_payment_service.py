"""Simulated QR payments (QR Simple style) collected by the platform account.

A real bank would call the webhook when the customer pays; in sandbox mode the
payer can trigger the same confirmation from the UI ("Simular pago")."""
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

try:
    import segno
except ImportError:
    segno = None
from sqlalchemy.orm import Session

from app.models.payout import QrPayment

QR_MINUTES = 15
PURPOSES = {"order", "sale", "reservation_deposit"}


def _payload(qr: QrPayment) -> str:
    return f"FASHIONSTORE|{qr.reference}|{qr.amount}|{qr.currency.upper()}"


def serialize(qr: QrPayment) -> dict:
    qr_img = segno.make(_payload(qr), error="m").png_data_uri(scale=6) if segno else ""
    return {
        "reference": qr.reference, "purpose": qr.purpose, "source_id": qr.source_id,
        "amount": qr.amount, "currency": qr.currency, "status": qr.status,
        "expires_at": qr.expires_at, "paid_at": qr.paid_at,
        "qr_payload": _payload(qr), "qr_image": qr_img,
    }


def create_qr(db: Session, *, tenant_id: UUID, purpose: str, amount, currency: str, created_by: UUID,
              source_id: UUID | None = None, branch_id: UUID | None = None) -> QrPayment:
    assert purpose in PURPOSES
    if Decimal(str(amount)) <= 0:
        raise ValueError("El monto a cobrar con QR debe ser mayor a cero")
    qr = QrPayment(
        tenant_id=tenant_id, reference="QR-" + secrets.token_hex(5).upper(), purpose=purpose,
        source_id=source_id, branch_id=branch_id, created_by=created_by,
        amount=Decimal(str(amount)).quantize(Decimal("0.01")), currency=currency.lower(),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=QR_MINUTES),
    )
    db.add(qr)
    db.flush()
    return qr


def get_qr(db: Session, reference: str, for_update: bool = False) -> QrPayment:
    query = db.query(QrPayment).filter(QrPayment.reference == reference)
    qr = (query.with_for_update() if for_update else query).first()
    if not qr:
        raise LookupError("Pago QR no encontrado")
    return qr


def confirm_qr_payment(db: Session, reference: str) -> QrPayment:
    """Bank notification: idempotent; fulfils orders and reservation deposits right away."""
    qr = get_qr(db, reference, for_update=True)
    if qr.status in {"paid", "used"}:
        return qr
    if qr.status != "pending" or qr.expires_at < datetime.now(timezone.utc):
        qr.status = "expired"
        db.commit()
        raise ValueError("El código QR expiró; genera uno nuevo")
    qr.status, qr.paid_at = "paid", datetime.now(timezone.utc)
    if qr.purpose == "order":
        from app.services.order_service import complete_qr_order
        complete_qr_order(db, qr)
        qr.status = "used"
    elif qr.purpose == "reservation_deposit":
        from app.services.reservation_service import complete_deposit_payment
        complete_deposit_payment(db, qr.source_id, "qr", qr.reference)
        qr.status = "used"
    # purpose "sale": stays "paid" until the cashier registers the sale with this reference.
    db.commit()
    db.refresh(qr)
    return qr


def consume_sale_qr(db: Session, reference: str, *, tenant_id: UUID, branch_id: UUID, amount, sale_id: UUID) -> QrPayment:
    qr = db.query(QrPayment).filter(QrPayment.reference == reference).with_for_update().first()
    if not qr or qr.purpose != "sale" or qr.tenant_id != tenant_id or qr.branch_id != branch_id:
        raise ValueError("El código QR no corresponde a esta caja")
    if qr.status == "used":
        raise ValueError("El código QR ya fue utilizado en otra venta")
    if qr.status != "paid":
        raise ValueError("El cliente aún no pagó el código QR")
    if qr.amount != Decimal(str(amount)).quantize(Decimal("0.01")):
        raise ValueError("El monto del QR no coincide con el total de la venta")
    qr.status, qr.source_id = "used", sale_id
    return qr
