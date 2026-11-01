from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.schemas.wishlist_schema import MoveAllToCartRequest, MoveToCartRequest, WishlistItemCreate
from app.services import wishlist_service as service
from app.utils.response import response


router = APIRouter(prefix="/wishlist", tags=["Wishlist"])
CUSTOMER = require_roles(RolEnum.cliente)


# [CU16 - Secuencia: Pasos 1.1, 3.9, 4.13, 5.13] WishlistPageComponent llama a list_route() de wishlist_routes (GET /api/wishlist)
# [CU16 - Secuencia: Pasos 1.6, 3.14, 4.18, 5.18] wishlist_routes retorna list_route(): 200 Lista de deseos obtenida exitosamente a WishlistPageComponent
# [CU16 - Secuencia: Paso 2.13] WishlistToggleButtonComponent llama a list_route() de wishlist_routes (GET /api/wishlist)
# [CU16 - Secuencia: Paso 2.18] wishlist_routes retorna list_route(): 200 Lista de deseos obtenida exitosamente a WishlistToggleButtonComponent
@router.get("")
def list_route(db: Session = Depends(get_db), user: dict = Depends(CUSTOMER)):
    return response(status_code=200, message="Lista de deseos obtenida exitosamente",
                    data=service.list_items(db, UUID(user["sub"])))


# [CU16 - Secuencia: Paso 2.5] WishlistToggleButtonComponent llama a add_route(payload) de wishlist_routes (POST /api/wishlist/items)
# [CU16 - Secuencia: Paso 2.12] wishlist_routes retorna add_route(payload): 201 Prenda añadida a tu lista de deseos a WishlistToggleButtonComponent
# [CU16 - Secuencia: Paso 5.5] WishlistPageComponent llama a add_route(payload) de wishlist_routes (POST /api/wishlist/items)
# [CU16 - Secuencia: Paso 5.12] wishlist_routes retorna add_route(payload): 201 Prenda añadida a tu lista de deseos a WishlistPageComponent
@router.post("/items", status_code=status.HTTP_201_CREATED)
def add_route(payload: WishlistItemCreate, db: Session = Depends(get_db), user: dict = Depends(CUSTOMER)):
    try:
        item = service.add_item(db, UUID(user["sub"]), payload.product_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except service.AlreadySaved as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return response(status_code=201, message="Prenda añadida a tu lista de deseos", data={"wishlist_item_id": item.id})


# [CU16 - Secuencia: Paso 2.1] WishlistToggleButtonComponent llama a remove_route(product_id) de wishlist_routes (DELETE /api/wishlist/items/{product_id})
# [CU16 - Secuencia: Paso 2.4] wishlist_routes retorna remove_route(product_id): 200 Prenda eliminada de tu lista de deseos a WishlistToggleButtonComponent
# [CU16 - Secuencia: Paso 5.1] WishlistPageComponent llama a remove_route(product_id) de wishlist_routes (DELETE /api/wishlist/items/{product_id})
# [CU16 - Secuencia: Paso 5.4] wishlist_routes retorna remove_route(product_id): 200 Prenda eliminada de tu lista de deseos a WishlistPageComponent
@router.delete("/items/{product_id}")
def remove_route(product_id: UUID, db: Session = Depends(get_db), user: dict = Depends(CUSTOMER)):
    try:
        service.remove_item(db, UUID(user["sub"]), product_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return response(status_code=200, message="Prenda eliminada de tu lista de deseos", data={"product_id": product_id})


# [CU16 - Secuencia: Paso 3.1] WishlistPageComponent llama a move_route(product_id, payload) de wishlist_routes (POST /api/wishlist/items/{product_id}/move-to-cart)
# [CU16 - Secuencia: Paso 3.8] wishlist_routes retorna move_route(product_id, payload): 200 Prenda movida al carrito de compras con éxito a WishlistPageComponent
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


# [CU16 - Secuencia: Paso 4.1] WishlistPageComponent llama a move_all_route(payload) de wishlist_routes (POST /api/wishlist/move-all-to-cart)
# [CU16 - Secuencia: Paso 4.12] wishlist_routes retorna move_all_route(payload): 200 Se agregaron ... prendas al carrito a WishlistPageComponent
@router.post("/move-all-to-cart")
def move_all_route(payload: MoveAllToCartRequest, db: Session = Depends(get_db), user: dict = Depends(CUSTOMER)):
    try:
        cart, count = service.move_all_to_cart(db, UUID(user["sub"]), payload.tenant_id, payload.branch_id, payload.clear_conflict)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=200, message=f"Se agregaron {count} prendas al carrito", data=cart.model_dump())

