from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_branch_id, require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.schemas.reservation_schema import ReservationCreate
from app.services.reservation_service import (
    attend_reservation,
    cancel_branch_reservation,
    cancel_reservation,
    create_reservation,
    confirm_reservation_arrival,
    get_reservation,
    list_reservations,
    list_reservations_by_branch,
)
from app.utils.response import response


router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.get("/me")
async def list_my_reservations_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    reservations = list_reservations(db, UUID(current_user["sub"]))
    return response(status_code=200, message="Reservas obtenidas exitosamente", data=reservations)


@router.get("/branch")
async def list_branch_reservations_route(
    db: Session = Depends(get_db),
    branch_id: UUID | None = Query(default=None),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    resolved_branch_id = branch_id or current_branch_id
    if resolved_branch_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="branch_id es requerido")

    if current_user.get("rol") != RolEnum.administrador.value and current_branch_id and resolved_branch_id != current_branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permisos para esta sucursal")

    reservations = list_reservations_by_branch(db, resolved_branch_id)
    return response(status_code=200, message="Reservas de sucursal obtenidas exitosamente", data=reservations)


@router.get("/{reservation_id}")
async def get_reservation_route(
    reservation_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    reservation = get_reservation(db, UUID(current_user["sub"]), reservation_id)
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reserva con id {reservation_id} no encontrada")
    return response(status_code=200, message="Reserva obtenida exitosamente", data=reservation)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_reservation_route(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        reservation = create_reservation(db, UUID(current_user["sub"]), payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=status.HTTP_201_CREATED, message="Reserva creada exitosamente", data=reservation)


@router.patch("/{reservation_id}/cancel")
async def cancel_reservation_route(
    reservation_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        reservation = cancel_reservation(db, UUID(current_user["sub"]), reservation_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reserva con id {reservation_id} no encontrada")
    return response(status_code=200, message="Reserva cancelada exitosamente", data=reservation)


@router.patch("/{reservation_id}/arrival")
async def confirm_reservation_arrival_route(
    reservation_id: UUID,
    db: Session = Depends(get_db),
    branch_id: UUID | None = Query(default=None),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    resolved_branch_id = branch_id or current_branch_id
    if resolved_branch_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="branch_id es requerido")

    try:
        reservation = confirm_reservation_arrival(db, reservation_id, resolved_branch_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reserva con id {reservation_id} no encontrada")
    return response(status_code=200, message="Llegada confirmada exitosamente", data=reservation)


@router.patch("/{reservation_id}/attend")
async def attend_reservation_route(
    reservation_id: UUID,
    db: Session = Depends(get_db),
    branch_id: UUID | None = Query(default=None),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    resolved_branch_id = branch_id or current_branch_id
    if resolved_branch_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="branch_id es requerido")

    try:
        reservation = attend_reservation(db, reservation_id, resolved_branch_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reserva con id {reservation_id} no encontrada")
    return response(status_code=200, message="Reserva atendida exitosamente", data=reservation)


@router.patch("/{reservation_id}/branch-cancel")
async def cancel_branch_reservation_route(
    reservation_id: UUID,
    db: Session = Depends(get_db),
    branch_id: UUID | None = Query(default=None),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    resolved_branch_id = branch_id or current_branch_id
    if resolved_branch_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="branch_id es requerido")

    try:
        reservation = cancel_branch_reservation(db, reservation_id, resolved_branch_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not reservation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reserva con id {reservation_id} no encontrada")
    return response(status_code=200, message="Reserva cancelada por sucursal exitosamente", data=reservation)
