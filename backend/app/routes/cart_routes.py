from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.schemas.cart_schema import CartItemCreate, CartItemUpdate
from app.schemas.enums import RolEnum
from app.services.cart_service import add_cart_item, clear_cart, get_current_cart, remove_cart_item, update_cart_item
from app.utils.response import response


router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("/current")
async def get_current_cart_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    cart = get_current_cart(db, UUID(current_user["sub"]))
    return response(status_code=200, message="Carrito obtenido exitosamente", data=cart.model_dump())


@router.post("/items", status_code=status.HTTP_201_CREATED)
async def add_cart_item_route(
    payload: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        cart = add_cart_item(db, UUID(current_user["sub"]), payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=status.HTTP_201_CREATED, message="Producto agregado al carrito", data=cart.model_dump())


@router.patch("/items/{item_id}")
async def update_cart_item_route(
    item_id: UUID,
    payload: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        cart = update_cart_item(db, UUID(current_user["sub"]), item_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=200, message="Carrito actualizado exitosamente", data=cart.model_dump())


@router.delete("/items/{item_id}")
async def delete_cart_item_route(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        cart = remove_cart_item(db, UUID(current_user["sub"]), item_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=200, message="Producto eliminado del carrito", data=cart.model_dump())


@router.delete("/current")
async def clear_cart_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    cart = clear_cart(db, UUID(current_user["sub"]))
    return response(status_code=200, message="Carrito vaciado exitosamente", data=cart.model_dump())
