import json
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.schemas.payment_schema import CashPaymentRequest, StripePaymentRequest, StripeCheckoutResponse
from app.services.order_service import checkout_cash, confirm_stripe_payment, create_stripe_payment
from app.utils.response import response


router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/cash/checkout")
async def cash_checkout_route(
    payload: CashPaymentRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        order = checkout_cash(db, UUID(current_user["sub"]), payload.cash_reference)
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
        order, client_secret = create_stripe_payment(db, UUID(current_user["sub"]), payload.currency or "usd")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(
        status_code=201,
        message="Pago con Stripe iniciado exitosamente",
        data=StripeCheckoutResponse(order_id=str(order["id"]), client_secret=client_secret, payment_intent_id=str(order.get("stripe_payment_intent_id") or "")).model_dump(),
    )


@router.post("/stripe/webhook")
async def stripe_webhook_route(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
):
    payload = await request.body()
    event = None

    try:
        import stripe
        from app.core.config import settings

        if settings.stripe_webhook_secret and stripe_signature:
            event = stripe.Webhook.construct_event(payload, stripe_signature, settings.stripe_webhook_secret)
        else:
            event = json.loads(payload.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Webhook inválido: {exc}") from exc

    event_type = event.get("type") if isinstance(event, dict) else event["type"]
    data_object = event.get("data", {}).get("object", {}) if isinstance(event, dict) else event["data"]["object"]
    payment_intent_id = data_object.get("id")

    if event_type == "payment_intent.succeeded" and payment_intent_id:
        order = confirm_stripe_payment(db, payment_intent_id, succeeded=True)
        return response(status_code=200, message="Pago confirmado", data=order)

    if event_type == "payment_intent.payment_failed" and payment_intent_id:
        order = confirm_stripe_payment(db, payment_intent_id, succeeded=False)
        return response(status_code=200, message="Pago marcado como fallido", data=order)

    return response(status_code=200, message="Evento ignorado", data={"event_type": event_type})
