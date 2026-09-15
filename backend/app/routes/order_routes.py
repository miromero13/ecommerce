from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_branch_id, get_current_user, require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.models.user import User
from app.schemas.payment_schema import CollectCashRequest
from app.services.order_service import cancel_order, collect_cash, get_order, list_orders, list_orders_by_branch, mark_order_ready
from app.utils.response import response


router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/me")
async def list_my_orders_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    orders = list_orders(db, UUID(current_user["sub"]))
    return response(status_code=200, message="Pedidos obtenidos exitosamente", data=orders)


@router.get("/branch")
async def list_branch_orders_route(
    db: Session = Depends(get_db),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
    _: dict = Depends(require_roles(RolEnum.encargado)),
):
    if current_branch_id is None:
        raise HTTPException(status_code=422, detail="El encargado no tiene sucursal asignada")
    return response(status_code=200, message="Pedidos de sucursal obtenidos", data=list_orders_by_branch(db, current_branch_id))


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


@router.post("/{order_id}/cancel")
async def cancel_order_route(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        order = cancel_order(db, UUID(current_user["sub"]), order_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado")
    return response(status_code=200, message="Pedido cancelado", data=order)


@router.post("/{order_id}/ready")
async def mark_order_ready_route(
    order_id: UUID,
    db: Session = Depends(get_db),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
    _: dict = Depends(require_roles(RolEnum.encargado)),
):
    if current_branch_id is None:
        raise HTTPException(status_code=422, detail="El encargado no tiene sucursal asignada")
    try:
        order = mark_order_ready(db, order_id, current_branch_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado en tu sucursal")
    return response(status_code=200, message="Pedido marcado como listo", data=order)


@router.post("/{order_id}/collect-cash")
async def collect_cash_route(
    order_id: UUID,
    payload: CollectCashRequest,
    db: Session = Depends(get_db),
    cashier: User = Depends(get_current_user),
    _: dict = Depends(require_roles(RolEnum.cajero)),
):
    try:
        order = collect_cash(db, order_id, payload.pickup_code, cashier.branch_id, cashier.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=200, message="Pedido cobrado y entregado", data=order)
