"""CU18: Gift cards issuance, purchase, verification, QR generation and email delivery."""
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
import secrets
import uuid
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

try:
    import segno
except ImportError:
    segno = None

from app.core.config import settings
from app.models.gift_card import GiftCard
from app.models.tenant import Tenant
from app.schemas.gift_card_schema import GiftCardPurchaseRequest
from app.services.email_service import email_service

MIN_AMOUNT = Decimal("10.00")
EXPIRATION_DAYS = 365
PENDING_PAYMENT = "pending_payment"


# [CU18 - Secuencia: Paso 2.4] gift_card_routes invoca generate_unique_code() sobre la entidad TarjetaRegalo
def generate_unique_code(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    for _ in range(20):
        suffix = secrets.token_hex(2).upper()  # 4 hex chars e.g. X89Q
        code = f"GIFT-{year}-{suffix}"
        if not db.query(GiftCard.id).filter(GiftCard.code == code).first():
            return code
    # Fallback to 4 random bytes
    return f"GIFT-{year}-{secrets.token_hex(4).upper()}"


def make_qr_data_uri(code: str) -> str:
    if not segno:
        return ""
    return segno.make(f"FASHIONSTORE|GIFTCARD|{code}", error="m").png_data_uri(scale=6)


def _amount_cents(amount: Decimal) -> int:
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


# [CU18 - Secuencia: Paso 2.6] gift_card_routes invoca _currency(tenant_id) sobre la entidad Empresa
def _currency(db: Session, tenant_id: UUID | None) -> str:
    """Las tarjetas de regalo se emiten en bolivianos (o en la moneda de la empresa emisora, si se indica)."""
    if tenant_id:
        currency = db.query(Tenant.currency).filter(Tenant.id == tenant_id).scalar()
        if currency:
            return currency.lower()
    return "bob"


# [CU18 - Secuencia: Paso 2.2] gift_card_routes invoca purchase_gift_card(buyer_id, payload) sobre la entidad TarjetaRegalo
def purchase_gift_card(db: Session, buyer_id: UUID, payload: GiftCardPurchaseRequest) -> tuple[GiftCard, str]:
    """Registra la tarjeta pendiente de pago y crea su PaymentIntent de Stripe.
    La tarjeta se activa recién cuando Stripe confirma el cobro (confirm_gift_card_payment o el webhook)."""
    amount = Decimal(str(payload.amount)).quantize(Decimal("0.01"))
    if amount < MIN_AMOUNT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El importe de la tarjeta de regalo debe ser mayor o igual a $10.00",
        )
    if payload.payment_method != "stripe":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las tarjetas de regalo se pagan con tarjeta a través de Stripe",
        )
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo iniciar el pago con Stripe: Stripe no está configurado",
        )

    code = generate_unique_code(db)
    qr_uri = make_qr_data_uri(code)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=EXPIRATION_DAYS)

    card = GiftCard(
        id=uuid.uuid4(),
        tenant_id=payload.tenant_id,
        buyer_id=buyer_id,
        code=code,
        amount=amount,
        balance=amount,
        recipient_name=payload.recipient_name,
        recipient_email=payload.recipient_email,
        custom_message=payload.custom_message,
        status=PENDING_PAYMENT,
        payment_method=payload.payment_method,
        qr_code_url=qr_uri,
        expires_at=expires,
        created_at=now,
    )
    import stripe

    stripe.api_key = settings.stripe_secret_key
    try:
        intent = stripe.PaymentIntent.create(
            amount=_amount_cents(amount),
            currency=_currency(db, payload.tenant_id),
            metadata={"gift_card_id": str(card.id)},
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
            idempotency_key=f"giftcard-{card.id}",
        )
    except Exception as exc:  # noqa: BLE001 - el error de Stripe se informa al cliente
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo iniciar el pago con Stripe: {exc}",
        ) from exc
    card.stripe_payment_intent_id = intent.id
    db.add(card)
    db.commit()
    db.refresh(card)
    return card, intent.client_secret


# [CU18 - Secuencia: Paso 3.4] gift_card_routes invoca activate_paid_gift_card(payment_intent) sobre la entidad TarjetaRegalo
def activate_paid_gift_card(db: Session, payment_intent) -> tuple[GiftCard, bool]:
    """Activa la tarjeta del PaymentIntent cobrado. Devuelve (tarjeta, True si se activó en esta llamada)."""
    card = (
        db.query(GiftCard)
        .filter(GiftCard.stripe_payment_intent_id == payment_intent["id"])
        .with_for_update()
        .first()
    )
    metadata = payment_intent.get("metadata") or {}
    if not card or metadata.get("gift_card_id") != str(card.id):
        raise ValueError("El PaymentIntent no coincide con la tarjeta de regalo")
    if card.status != PENDING_PAYMENT:
        return card, False
    if payment_intent.get("amount") != _amount_cents(card.amount):
        raise ValueError("El PaymentIntent no coincide con el importe de la tarjeta de regalo")
    card.status = "active"
    db.commit()
    db.refresh(card)
    return card, True


# [CU18 - Secuencia: Paso 3.2] gift_card_routes invoca confirm_gift_card_payment(buyer_id, card_id) sobre la entidad TarjetaRegalo
def confirm_gift_card_payment(db: Session, buyer_id: UUID, card_id: UUID) -> tuple[GiftCard, bool]:
    """Consulta a Stripe el PaymentIntent de la tarjeta y la activa si el cobro se completó."""
    card = db.query(GiftCard).filter(GiftCard.id == card_id, GiftCard.buyer_id == buyer_id).first()
    if not card or not card.stripe_payment_intent_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarjeta de regalo no encontrada")
    if card.status != PENDING_PAYMENT:
        return card, False
    import stripe

    stripe.api_key = settings.stripe_secret_key
    intent = stripe.PaymentIntent.retrieve(card.stripe_payment_intent_id)
    if intent["status"] != "succeeded":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El pago con tarjeta todavía no se confirmó. La tarjeta se emitirá al confirmarse el cobro.",
        )
    try:
        return activate_paid_gift_card(db, intent)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


async def send_gift_card_email(card: GiftCard) -> None:
    subject = f"¡Recibiste una Tarjeta de Regalo de {card.recipient_name}!"
    custom_msg_html = f"<p style='font-style: italic; color: #555;'>\"{card.custom_message}\"</p>" if card.custom_message else ""
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 16px; overflow: hidden; background: #ffffff;">
      <div style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); padding: 32px; text-align: center; color: white;">
        <h1 style="margin: 0; font-size: 24px; font-weight: 700;">¡Tienes un Regalo Especial!</h1>
        <p style="margin-top: 8px; opacity: 0.9;">Tarjeta de Regalo Fashion Store</p>
      </div>
      <div style="padding: 32px; text-align: center;">
        <p style="font-size: 16px; color: #334155;">Hola <strong>{card.recipient_name}</strong>,</p>
        {custom_msg_html}
        <div style="margin: 24px auto; padding: 20px; background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 12px; display: inline-block;">
          <p style="margin: 0 0 8px 0; font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 1px;">Código de Canje</p>
          <p style="margin: 0; font-size: 28px; font-weight: 800; color: #1e293b; letter-spacing: 2px;">{card.code}</p>
          <p style="margin: 8px 0 0 0; font-size: 18px; font-weight: 600; color: #10b981;">Valor: ${card.amount:.2f} BOB</p>
        </div>
        {f'<div style="margin-top: 16px;"><img src="{card.qr_code_url}" alt="QR Gift Card" style="width: 180px; height: 180px;" /></div>' if card.qr_code_url else ''}
        <p style="margin-top: 24px; font-size: 14px; color: #64748b;">
          Podés canjear esta tarjeta acreditando el saldo en tu <strong>Billetera Digital</strong> desde la web o la app móvil.
        </p>
      </div>
    </div>
    """
    await email_service.send_email(
        to=card.recipient_email,
        subject=subject,
        html=html,
        text=f"¡Hola {card.recipient_name}! Recibiste una tarjeta de regalo por ${card.amount:.2f}. Tu código es {card.code}.",
        category="gift_card",
    )


# [CU18 - Secuencia: Pasos 1.2, 3.8] gift_card_routes invoca list_my_purchases(buyer_id) sobre la entidad TarjetaRegalo
def list_my_purchases(db: Session, buyer_id: UUID) -> list[GiftCard]:
    return (
        db.query(GiftCard)
        .filter(GiftCard.buyer_id == buyer_id, GiftCard.status != PENDING_PAYMENT)
        .order_by(GiftCard.created_at.desc())
        .all()
    )


def verify_gift_card(db: Session, code: str) -> GiftCard:
    cleaned = code.strip().upper()
    card = db.query(GiftCard).filter(GiftCard.code == cleaned).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarjeta de regalo no encontrada con el código ingresado",
        )
    return card
