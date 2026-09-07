from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_branch_id, require_roles
from app.core.database import get_db
from app.models.user import User
from app.schemas.enums import RolEnum
from app.schemas.inventory_schema import InventoryMovementCreate, InventoryTransferCreate, InventoryMovementTypeEnum
from app.services.inventory_service import (
    get_branch_stock,
    get_consolidated_stock,
    list_movements,
    register_income,
    register_outcome,
    register_transfer,
)
from app.utils.response import response


router = APIRouter(prefix="/inventory", tags=["Inventory"])


def _require_branch_access(current_user: dict, branch_id: UUID) -> None:
    if current_user.get("rol") == RolEnum.administrador.value:
        return
    current_branch_id = current_user.get("branch_id")
    if not current_branch_id or UUID(current_branch_id) != branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para esta sucursal")


@router.get("/consolidated")
async def consolidated_stock_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
):
    stock = get_consolidated_stock(db)
    return response(status_code=200, message="Inventario consolidado obtenido exitosamente", data=stock)


@router.get("/branches/{branch_id}")
async def branch_stock_route(
    branch_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado, RolEnum.cajero)),
):
    _require_branch_access(current_user, branch_id)
    stock = get_branch_stock(db, branch_id)
    return response(status_code=200, message="Inventario por sucursal obtenido exitosamente", data=stock)


@router.get("/movements")
async def movements_route(
    db: Session = Depends(get_db),
    variant_id: UUID | None = None,
    branch_id: UUID | None = None,
    movement_type: InventoryMovementTypeEnum | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado, RolEnum.cajero)),
):
    if branch_id is not None:
        _require_branch_access(current_user, branch_id)

    movements = list_movements(db, variant_id=variant_id, branch_id=branch_id, movement_type=movement_type, limit=limit)
    return response(status_code=200, message="Movimientos de inventario obtenidos exitosamente", data=movements)


@router.post("/movements/income", status_code=status.HTTP_201_CREATED)
async def income_route(
    payload: InventoryMovementCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
): 
    _require_branch_access(current_user, payload.branch_id)
    try:
        created_by = UUID(current_user["sub"]) if current_user.get("sub") else None
        movement, inventory = register_income(db, payload, created_by=created_by)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(
        status_code=status.HTTP_201_CREATED,
        message="Ingreso de inventario registrado exitosamente",
        data={"movement": movement.id, "variant_id": inventory.variant_id, "branch_id": inventory.branch_id, "quantity": inventory.quantity},
    )


@router.post("/movements/outcome", status_code=status.HTTP_201_CREATED)
async def outcome_route(
    payload: InventoryMovementCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
): 
    _require_branch_access(current_user, payload.branch_id)
    try:
        created_by = UUID(current_user["sub"]) if current_user.get("sub") else None
        movement, inventory = register_outcome(db, payload, created_by=created_by)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(
        status_code=status.HTTP_201_CREATED,
        message="Salida de inventario registrada exitosamente",
        data={"movement": movement.id, "variant_id": inventory.variant_id, "branch_id": inventory.branch_id, "quantity": inventory.quantity},
    )


@router.post("/movements/transfer", status_code=status.HTTP_201_CREATED)
async def transfer_route(
    payload: InventoryTransferCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
): 
    try:
        created_by = UUID(current_user["sub"]) if current_user.get("sub") else None
        movements, inventories = register_transfer(db, payload, created_by=created_by)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(
        status_code=status.HTTP_201_CREATED,
        message="Traspaso de inventario registrado exitosamente",
        data={
            "movements": [movement.id for movement in movements],
            "variant_id": inventories[0].variant_id,
            "from_branch_id": inventories[0].branch_id,
            "to_branch_id": inventories[1].branch_id,
        },
    )
