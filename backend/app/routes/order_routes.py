from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.services.order_service import get_order, list_orders
from app.utils.response import response


router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/me")
async def list_my_orders_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    orders = list_orders(db, UUID(current_user["sub"]))
    return response(status_code=200, message="Pedidos obtenidos exitosamente", data=orders)


@router.get("/{order_id}")
async def get_order_route(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    order = get_order(db, UUID(current_user["sub"]), order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Pedido con id {order_id} no encontrado")
    return response(status_code=200, message="Pedido obtenido exitosamente", data=order)
