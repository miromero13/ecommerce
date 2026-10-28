from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.schemas.wishlist_schema import MoveToCartRequest, WishlistItemCreate
from app.services import wishlist_service as service
from app.utils.response import response


router = APIRouter(prefix="/wishlist", tags=["Wishlist"])
CUSTOMER = require_roles(RolEnum.cliente)


@router.get("")
def list_route(db: Session = Depends(get_db), user: dict = Depends(CUSTOMER)):
    return response(status_code=200, message="Lista de deseos obtenida exitosamente",
                    data=service.list_items(db, UUID(user["sub"])))


@router.post("/items", status_code=status.HTTP_201_CREATED)
def add_route(payload: WishlistItemCreate, db: Session = Depends(get_db), user: dict = Depends(CUSTOMER)):
    try:
        item = service.add_item(db, UUID(user["sub"]), payload.product_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except service.AlreadySaved as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return response(status_code=201, message="Prenda añadida a tu lista de deseos", data={"wishlist_item_id": item.id})


@router.delete("/items/{product_id}")
def remove_route(product_id: UUID, db: Session = Depends(get_db), user: dict = Depends(CUSTOMER)):
    try:
        service.remove_item(db, UUID(user["sub"]), product_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return response(status_code=200, message="Prenda eliminada de tu lista de deseos", data={"product_id": product_id})


@router.post("/items/{product_id}/move-to-cart")
def move_route(product_id: UUID, payload: MoveToCartRequest, db: Session = Depends(get_db),
               user: dict = Depends(CUSTOMER)):
    try:
        cart = service.move_to_cart(db, UUID(user["sub"]), product_id, payload.variant_id, payload.branch_id, payload.quantity)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=200, message="Prenda movida al carrito de compras con éxito", data=cart)
