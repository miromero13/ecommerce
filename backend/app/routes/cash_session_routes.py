from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.core.database import get_db
from app.models.user import User
from app.schemas.cash_session_schema import CashMovementCreate, CashSessionClose, CashSessionOpen
from app.schemas.enums import RolEnum
from app.services import cash_session_service as service
from app.utils.response import response


router = APIRouter(prefix="/cash-sessions", tags=["Cash sessions"])
CASHIER = require_roles(RolEnum.cajero)
VIEWERS = require_roles(RolEnum.administrador, RolEnum.encargado, RolEnum.cajero)


def _scope(user: User, branch_id: UUID | None) -> dict:
    """Admin: any branch of the company. Manager: only their branch. Cashier: only their own drawers."""
    if user.rol == RolEnum.administrador:
        return {"branch_id": branch_id}
    if user.rol == RolEnum.encargado:
        return {"branch_id": user.branch_id}
    return {"branch_id": user.branch_id, "cashier_id": user.id}


@router.get("/current")
def current_route(db: Session = Depends(get_db), user: User = Depends(get_current_user), _: dict = Depends(CASHIER)):
    session = service.get_open_session(db, user.id)
    return response(status_code=200, message="Caja obtenida exitosamente" if session else "No tienes una caja abierta",
                    data=service.serialize(db, session) if session else None)


@router.post("/open", status_code=status.HTTP_201_CREATED)
def open_route(payload: CashSessionOpen, db: Session = Depends(get_db), user: User = Depends(get_current_user),
               _: dict = Depends(CASHIER)):
    try:
        session = service.open_session(db, user, payload.opening_amount)
    except service.CashSessionConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=201, message="Caja abierta exitosamente", data=session)


@router.post("/current/movements", status_code=status.HTTP_201_CREATED)
def movement_route(payload: CashMovementCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user),
                   _: dict = Depends(CASHIER)):
    try:
        session = service.add_manual_movement(db, user, payload.type, payload.amount, payload.reason)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    label = "Retiro" if payload.type == "withdrawal" else "Ingreso"
    return response(status_code=201, message=f"{label} de efectivo registrado", data=session)


@router.post("/current/close")
def close_route(payload: CashSessionClose, db: Session = Depends(get_db), user: User = Depends(get_current_user),
                _: dict = Depends(CASHIER)):
    try:
        session = service.close_session(db, user, payload.counted_amount, payload.note)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    difference = session["difference"]
    result = "la caja cuadra" if difference == 0 else (f"sobrante de {difference} Bs." if difference > 0 else f"faltante de {-difference} Bs.")
    return response(status_code=200, message=f"Caja cerrada: {result}", data=session)


@router.get("")
def list_route(
    branch_id: UUID | None = Query(default=None),
    day: date | None = Query(default=None, description="Día de apertura (AAAA-MM-DD)"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _: dict = Depends(VIEWERS),
):
    return response(status_code=200, message="Cajas obtenidas exitosamente",
                    data=service.list_sessions(db, user.tenant_id, day=day, **_scope(user, branch_id)))


@router.get("/{session_id}")
def detail_route(session_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user),
                 _: dict = Depends(VIEWERS)):
    session = service.get_session(db, session_id, user.tenant_id, **_scope(user, None))
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caja no encontrada")
    return response(status_code=200, message="Caja obtenida exitosamente", data=session)
