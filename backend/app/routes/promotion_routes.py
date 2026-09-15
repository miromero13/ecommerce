from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.schemas.promotion_schema import PromotionCodeCreate, PromotionCodeRead
from app.services.promotion_service import create_code, list_codes
from app.utils.response import response


router = APIRouter(prefix="/promotions", tags=["Promotions"])


@router.get("")
async def get_promotion_codes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    branch_id = None if current_user.get("rol") == RolEnum.administrador.value else UUID(current_user["branch_id"])
    return response(status_code=200, message="Códigos promocionales obtenidos", data=[PromotionCodeRead.model_validate(item).model_dump() for item in list_codes(db, branch_id)])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_promotion_code(
    payload: PromotionCodeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    role = current_user.get("rol")
    if role == RolEnum.administrador.value:
        if payload.branch_id is not None:
            raise HTTPException(status_code=400, detail="El administrador solo puede crear códigos globales")
    elif payload.branch_id is None or payload.branch_id != UUID(current_user["branch_id"]):
        raise HTTPException(status_code=403, detail="El código debe pertenecer a la sucursal del encargado")

    try:
        item = create_code(db, payload, UUID(current_user["sub"]))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return response(status_code=201, message="Código promocional creado", data=PromotionCodeRead.model_validate(item).model_dump())
