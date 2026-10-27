from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_branch_id, get_current_payload, get_current_tenant_id, get_current_user, require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.schemas.payment_schema import CashPaymentRequest, QrWebhook, StripePaymentRequest, StripeCheckoutResponse
from app.schemas.sales_schema import SaleCreate
from app.services.order_service import checkout_cash, checkout_qr, create_deposit_stripe_payment, create_stripe_payment, create_stripe_payment_for_order, process_stripe_event
from app.services.qr_payment_service import confirm_qr_payment, create_qr, get_qr, serialize as serialize_qr
from app.services.sales_service import quote_sale_total
from app.utils.response import response


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/cash/checkout")
async def cash_checkout_route(
    payload: CashPaymentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        order = checkout_cash(db, UUID(current_user["sub"]), payload.pickup_branch_id, payload.delivery)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=201, message="Pago en efectivo procesado exitosamente", data=order)


@router.post("/stripe/checkout")
async def stripe_checkout_route(
    payload: StripePaymentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        order, client_secret, payment_intent_id = create_stripe_payment(db, UUID(current_user["sub"]), payload.pickup_branch_id, payload.delivery)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(
        status_code=201,
        message="Pago con Stripe iniciado exitosamente",
        data=StripeCheckoutResponse(order_id=str(order["id"]), client_secret=client_secret, payment_intent_id=payment_intent_id, pickup_expires_at=order["pickup_expires_at"].isoformat()).model_dump(),
    )


@router.post("/stripe/orders/{order_id}")
async def stripe_order_payment_route(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        order, client_secret, payment_intent_id = create_stripe_payment_for_order(
            db, UUID(current_user["sub"]), order_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(
        status_code=200,
        message="Pago con Stripe iniciado exitosamente",
        data=StripeCheckoutResponse(
            order_id=str(order["id"]),
            client_secret=client_secret,
            payment_intent_id=payment_intent_id,
            pickup_expires_at=order["pickup_expires_at"].isoformat(),
        ).model_dump(),
    )


@router.post("/stripe/webhook")
async def stripe_webhook_route(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    payload = await request.body()
    try:
        import stripe
        from app.core.config import settings

        if not settings.stripe_webhook_secret or not stripe_signature:
            raise ValueError("Falta la firma o el secreto del webhook")
        event = stripe.Webhook.construct_event(payload, stripe_signature, settings.stripe_webhook_secret)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Webhook inválido: {exc}") from exc

    try:
        process_stripe_event(db, event)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=200, message="Evento recibido", data={"event_type": event["type"]})


# --- Simulated QR payments (platform collection account) -------------------------------------

def _qr_access(db: Session, qr, payload: dict) -> None:
    """The QR's creator, or staff of its company, may follow and (in sandbox) confirm it."""
    same_company = payload.get("tenant_id") and str(qr.tenant_id) == payload["tenant_id"]
    if str(qr.created_by) != payload["sub"] and not same_company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago QR no encontrado")


@router.post("/qr/checkout", status_code=status.HTTP_201_CREATED)
async def qr_checkout_route(
    payload: CashPaymentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        order, qr = checkout_qr(db, UUID(current_user["sub"]), payload.pickup_branch_id, payload.delivery)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=201, message="Pedido creado. Escanea el código QR para pagar.", data={"order": order, "qr": qr})


@router.post("/qr/sale-intent", status_code=status.HTTP_201_CREATED)
async def qr_sale_intent_route(
    payload: SaleCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cajero)),
    branch_id: UUID | None = Depends(get_current_branch_id),
    tenant_id: UUID | None = Depends(get_current_tenant_id),
):
    from app.models.tenant import Tenant

    try:
        total = quote_sale_total(db, UUID(current_user["sub"]), payload, branch_id, tenant_id)
        currency = db.query(Tenant.currency).filter(Tenant.id == tenant_id).scalar()
        qr = create_qr(db, tenant_id=tenant_id, purpose="sale", amount=total, currency=currency,
                       created_by=UUID(current_user["sub"]), branch_id=branch_id)
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=201, message="Código QR generado. Pide al cliente que lo escanee.", data=serialize_qr(qr))


@router.get("/qr/{reference}")
async def qr_status_route(reference: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_payload)):
    try:
        qr = get_qr(db, reference)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    _qr_access(db, qr, current_user)
    return response(status_code=200, message="Estado del pago QR obtenido", data=serialize_qr(qr))


@router.post("/qr/{reference}/simulate-payment")
async def qr_simulate_route(reference: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_payload)):
    from app.core.config import settings

    if not settings.qr_sandbox:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La simulación de pagos QR está deshabilitada")
    try:
        _qr_access(db, get_qr(db, reference), current_user)
        qr = confirm_qr_payment(db, reference)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=200, message="Pago QR confirmado", data=serialize_qr(qr))


@router.post("/qr/webhook")
async def qr_webhook_route(body: QrWebhook, db: Session = Depends(get_db),
                           secret: str | None = Header(default=None, alias="X-QR-Webhook-Secret")):
    from app.core.config import settings

    if not settings.qr_webhook_secret or secret != settings.qr_webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Firma del banco inválida")
    try:
        qr = confirm_qr_payment(db, body.reference)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=200, message="Pago QR registrado", data={"reference": qr.reference, "status": qr.status})



# --- D1: 50 % non-refundable reservation deposit (card or QR) ---------------------------------

@router.post("/qr/reservations/{reservation_id}", status_code=status.HTTP_201_CREATED)
async def deposit_qr_route(reservation_id: UUID, db: Session = Depends(get_db),
                           current_user: dict = Depends(require_roles(RolEnum.cliente))):
    from app.models.tenant import Tenant
    from app.services.reservation_service import get_deposit_reservation

    try:
        reservation = get_deposit_reservation(db, UUID(current_user["sub"]), reservation_id)
        currency = db.query(Tenant.currency).filter(Tenant.id == reservation.tenant_id).scalar()
        qr = create_qr(db, tenant_id=reservation.tenant_id, purpose="reservation_deposit",
                       amount=reservation.deposit_amount, currency=currency,
                       created_by=UUID(current_user["sub"]), source_id=reservation.id)
        qr.expires_at = reservation.payment_expires_at
        db.commit()
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=201, message="Escanea el código QR para pagar el anticipo del 50 %", data=serialize_qr(qr))


@router.post("/stripe/reservations/{reservation_id}")
async def deposit_stripe_route(reservation_id: UUID, db: Session = Depends(get_db),
                               current_user: dict = Depends(require_roles(RolEnum.cliente))):
    try:
        client_secret, intent_id = create_deposit_stripe_payment(db, UUID(current_user["sub"]), reservation_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"No se pudo iniciar el pago con Stripe: {exc}") from exc
    return response(status_code=200, message="Pago del anticipo con tarjeta iniciado",
                    data={"client_secret": client_secret, "payment_intent_id": intent_id})
