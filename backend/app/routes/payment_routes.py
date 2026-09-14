from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.schemas.payment_schema import CashPaymentRequest, StripePaymentRequest, StripeCheckoutResponse
from app.services.order_service import checkout_cash, create_stripe_payment, process_stripe_event
from app.utils.response import response


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/cash/checkout")
async def cash_checkout_route(
    payload: CashPaymentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        order = checkout_cash(db, UUID(current_user["sub"]), payload.pickup_branch_id)
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
        order, client_secret, payment_intent_id = create_stripe_payment(db, UUID(current_user["sub"]), payload.pickup_branch_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(
        status_code=201,
        message="Pago con Stripe iniciado exitosamente",
        data=StripeCheckoutResponse(order_id=str(order["id"]), client_secret=client_secret, payment_intent_id=payment_intent_id, pickup_expires_at=order["pickup_expires_at"].isoformat()).model_dump(),
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
