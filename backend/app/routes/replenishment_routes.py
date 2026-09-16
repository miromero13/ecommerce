from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.schemas.replenishment_schema import ReplenishmentRequestCreate, ReplenishmentStatusUpdate
from app.services.replenishment_service import create_request, list_requests, serialize_requests, transition_request
from app.utils.response import response

router = APIRouter(prefix="/replenishment", tags=["Replenishment"])
ALL = require_roles(RolEnum.administrador, RolEnum.proveedor, RolEnum.encargado)

@router.get("/requests")
def get_requests(db: Session = Depends(get_db), current_user: dict = Depends(ALL)):
    branch_id = UUID(current_user["branch_id"]) if current_user.get("branch_id") else None
    return response(200, "Solicitudes obtenidas exitosamente", serialize_requests(db, list_requests(db, current_user["rol"], UUID(current_user["sub"]), branch_id)))

@router.post("/requests", status_code=status.HTTP_201_CREATED)
def post_request(payload: ReplenishmentRequestCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_roles(RolEnum.administrador))):
    try:
        request = create_request(db, payload, UUID(current_user["sub"]))
        return response(201, "Solicitud creada exitosamente", serialize_requests(db, [request])[0])
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

@router.patch("/requests/{request_id}/status")
def patch_status(request_id: UUID, payload: ReplenishmentStatusUpdate, db: Session = Depends(get_db), current_user: dict = Depends(ALL)):
    branch_id = UUID(current_user["branch_id"]) if current_user.get("branch_id") else None
    try:
        request = transition_request(db, request_id, payload.status, current_user["rol"], UUID(current_user["sub"]), branch_id)
        return response(200, "Estado actualizado exitosamente", serialize_requests(db, [request])[0])
    except LookupError as exc:
        raise HTTPException(404, str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
