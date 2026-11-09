from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.schemas.gift_card_schema import (
    GiftCardPurchaseRequest,
    GiftCardResponse,
    GiftCardVerifyResponse,
)
from app.services import gift_card_service as service
from app.utils.response import response

router = APIRouter(prefix="/gift-cards", tags=["GiftCards"])
CUSTOMER = require_roles(RolEnum.cliente)


# [CU18 - Secuencia: Paso 2.1] GiftCardsPageComponent llama a purchase_route(payload) de gift_card_routes (POST /api/gift-cards/purchase)
@router.post("/purchase", status_code=status.HTTP_201_CREATED)
async def purchase_route(
    payload: GiftCardPurchaseRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: dict = Depends(CUSTOMER),
):
    card, client_secret = service.purchase_gift_card(db, UUID(user["sub"]), payload)
    return response(
        status_code=status.HTTP_201_CREATED,
        message="Pago con Stripe iniciado: ingresa los datos de la tarjeta",
        data={
            "id": str(card.id),
            "client_secret": client_secret,
            "amount": float(card.amount),
            "status": card.status,
        },
    )


# [CU18 - Secuencia: Paso 3.1] GiftCardsPageComponent llama a confirm_payment_route(card_id) de gift_card_routes (POST /api/gift-cards/{card_id}/confirm-payment)
@router.post("/{card_id}/confirm-payment")
async def confirm_payment_route(
    card_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: dict = Depends(CUSTOMER),
):
    card, activated = service.confirm_gift_card_payment(db, UUID(user["sub"]), card_id)
    if activated:
        background_tasks.add_task(service.send_gift_card_email, card)
    return response(
        status_code=status.HTTP_200_OK,
        message="Tarjeta de regalo adquirida y enviada por correo al destinatario",
        data={
            "id": str(card.id),
            "card_code": card.code,
            "qr_code_url": card.qr_code_url,
            "amount": float(card.amount),
            "recipient_name": card.recipient_name,
            "recipient_email": card.recipient_email,
            "expires_at": card.expires_at.isoformat() if card.expires_at else None,
        },
    )


# [CU18 - Secuencia: Pasos 1.1, 3.7] GiftCardsPageComponent llama a my_purchases_route() de gift_card_routes (GET /api/gift-cards/my-purchases)
@router.get("/my-purchases")
def my_purchases_route(
    db: Session = Depends(get_db),
    user: dict = Depends(CUSTOMER),
):
    cards = service.list_my_purchases(db, UUID(user["sub"]))
    data = [
        GiftCardResponse.model_validate(card).model_dump(mode="json")
        for card in cards
    ]
    return response(
        status_code=status.HTTP_200_OK,
        message="Tarjetas de regalo obtenidas exitosamente",
        data=data,
    )


@router.get("/verify/{code}")
def verify_route(
    code: str,
    db: Session = Depends(get_db),
):
    card = service.verify_gift_card(db, code)
    data = GiftCardVerifyResponse(
        code=card.code,
        amount=card.amount,
        balance=card.balance,
        status=card.status,
        recipient_name=card.recipient_name,
        expires_at=card.expires_at,
    ).model_dump(mode="json")
    return response(
        status_code=status.HTTP_200_OK,
        message="Tarjeta de regalo verificada exitosamente",
        data=data,
    )
