from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.schemas.wallet_schema import (
    WalletCheckoutRequest,
    WalletConvertPointsRequest,
    WalletPayRequest,
    WalletRedeemRequest,
)
from app.services import wallet_service as service
from app.utils.response import response

router = APIRouter(prefix="/wallet", tags=["Wallet"])
CUSTOMER = require_roles(RolEnum.cliente)


@router.get("/balance")
def balance_route(
    db: Session = Depends(get_db),
    user: dict = Depends(CUSTOMER),
):
    data = service.get_wallet_balance(db, UUID(user["sub"]))
    return response(
        status_code=status.HTTP_200_OK,
        message="Saldo de billetera virtual obtenido",
        data=data,
    )


@router.post("/redeem-gift-card")
def redeem_gift_card_route(
    payload: WalletRedeemRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(CUSTOMER),
):
    result = service.redeem_gift_card(db, UUID(user["sub"]), payload.card_code)
    return response(
        status_code=status.HTTP_200_OK,
        message=f"Gift Card canjeada exitosamente. Se acreditaron ${result['credited_amount']:.2f} en tu saldo.",
        data=result,
    )


@router.post("/convert-points")
def convert_points_route(
    payload: WalletConvertPointsRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(CUSTOMER),
):
    result = service.convert_loyalty_points(
        db,
        user_id=UUID(user["sub"]),
        tenant_id=payload.tenant_id,
        points=payload.points,
    )
    return response(
        status_code=status.HTTP_200_OK,
        message=f"Puntos convertidos exitosamente: se acreditaron ${result['credited_amount']:.2f} BOB en tu saldo.",
        data=result,
    )


@router.post("/pay")
def pay_route(
    payload: WalletPayRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(CUSTOMER),
):
    service.pay_order_with_wallet(db, UUID(user["sub"]), payload.order_id, payload.amount_to_debit)
    return response(
        status_code=status.HTTP_200_OK,
        message="Pago debitado exitosamente de la billetera virtual",
        data={"order_id": str(payload.order_id)},
    )


@router.post("/checkout")
def checkout_route(
    payload: WalletCheckoutRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(CUSTOMER),
):
    order = service.checkout_with_wallet(
        db,
        UUID(user["sub"]),
        payload.pickup_branch_id,
        payload.delivery,
        payload.points_to_redeem,
    )
    return response(
        status_code=status.HTTP_201_CREATED,
        message="Pedido pagado exitosamente con tu Billetera Digital",
        data=order,
    )


@router.get("/transactions")
def transactions_route(
    db: Session = Depends(get_db),
    user: dict = Depends(CUSTOMER),
):
    data = service.list_transactions(db, UUID(user["sub"]))
    # Convert dates to ISO strings for JSON serialization
    serialized = [
        {
            **tx,
            "id": str(tx["id"]),
            "source_id": str(tx["source_id"]) if tx.get("source_id") else None,
            "created_at": tx["created_at"].isoformat() if tx.get("created_at") else None,
        }
        for tx in data
    ]
    return response(
        status_code=status.HTTP_200_OK,
        message="Movimientos de billetera obtenidos exitosamente",
        data=serialized,
    )
