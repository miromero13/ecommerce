from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_branch_id, require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.schemas.sales_schema import SaleCreate
from app.services.sales_service import create_sale, get_sale, list_sales_by_branch
from app.utils.response import response


router = APIRouter(prefix="/sales", tags=["Sales"])


def _resolve_branch_id(requested_branch_id: UUID | None, current_branch_id: UUID | None) -> UUID | None:
    return requested_branch_id or current_branch_id


@router.get("/branch")
async def list_branch_sales_route(
    db: Session = Depends(get_db),
    branch_id: UUID | None = Query(default=None),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado, RolEnum.cajero)),
):
    resolved_branch_id = _resolve_branch_id(branch_id, current_branch_id)
    if resolved_branch_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="branch_id es requerido")

    if current_user.get("rol") != RolEnum.administrador.value and current_branch_id and resolved_branch_id != current_branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para esta sucursal")

    sales = list_sales_by_branch(db, resolved_branch_id)
    return response(status_code=200, message="Ventas de sucursal obtenidas exitosamente", data=sales)


@router.get("/{sale_id}")
async def get_sale_route(
    sale_id: UUID,
    db: Session = Depends(get_db),
    branch_id: UUID | None = Query(default=None),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado, RolEnum.cajero)),
):
    resolved_branch_id = _resolve_branch_id(branch_id, current_branch_id)
    if resolved_branch_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="branch_id es requerido")

    if current_user.get("rol") != RolEnum.administrador.value and current_branch_id and resolved_branch_id != current_branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para esta sucursal")

    sale = get_sale(db, resolved_branch_id, sale_id)
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Venta con id {sale_id} no encontrada")
    return response(status_code=200, message="Venta obtenida exitosamente", data=sale)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_sale_route(
    payload: SaleCreate,
    db: Session = Depends(get_db),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado, RolEnum.cajero)),
):
    resolved_branch_id = payload.branch_id or current_branch_id
    if resolved_branch_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="branch_id es requerido")

    if current_user.get("rol") != RolEnum.administrador.value and current_branch_id and resolved_branch_id != current_branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para esta sucursal")

    try:
        sale = create_sale(db, UUID(current_user["sub"]), payload, resolved_branch_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=status.HTTP_201_CREATED, message="Venta registrada exitosamente", data=sale)
