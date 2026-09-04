from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.auth.dependencies import require_roles
from app.auth.dependencies import get_current_branch_id
from app.core.database import get_db
from app.models.user import User
from app.schemas.branch_schema import BranchCreate, BranchRead
from app.schemas.enums import RolEnum
from app.services.branch_service import create_branch, get_branches
from app.utils.response import response


router = APIRouter(prefix="/branches", tags=["Branches"])


@router.get("/")
async def list_branches_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
):
    branches = get_branches(db, current_branch_id)
    branches_data = [BranchRead.model_validate(branch).model_dump() for branch in branches]
    return response(
        status_code=status.HTTP_200_OK,
        message="Sucursales obtenidas exitosamente",
        data=branches_data,
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_branch_route(
    branch: BranchCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
):
    if current_branch_id is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes crear sucursales desde una sucursal asignada")

    try:
        db_branch = create_branch(db, branch)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    branch_data = BranchRead.model_validate(db_branch).model_dump()
    return response(
        status_code=status.HTTP_201_CREATED,
        message="Sucursal creada exitosamente",
        data=branch_data,
    )


@router.get("/public")
async def list_public_branches_route(db: Session = Depends(get_db)):
    branches = get_branches(db)
    branches_data = [BranchRead.model_validate(branch).model_dump() for branch in branches]
    return response(
        status_code=status.HTTP_200_OK,
        message="Sucursales obtenidas exitosamente",
        data=branches_data,
    )
