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


@router.post("/purchase", status_code=status.HTTP_201_CREATED)
async def purchase_route(
    payload: GiftCardPurchaseRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: dict = Depends(CUSTOMER),
):
    card = service.purchase_gift_card(db, UUID(user["sub"]), payload)
    background_tasks.add_task(service.send_gift_card_email, card)
    return response(
        status_code=status.HTTP_201_CREATED,
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
