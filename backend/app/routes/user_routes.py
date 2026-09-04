from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.schemas.user_schema import UserCreate, UserRead, UsersPaginatedResponse, UserUpdateRol, UserUpdateBranch
from app.services.user_service import create_user, get_user, get_users, get_users_count, update_user_rol, update_user_branch
from app.core.database import get_db
from app.utils.response import response
from app.auth.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.enums import RolEnum

router = APIRouter(prefix="/users", tags=["Users"])

# 🚀 Crea usuario (público)
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user_route(user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = create_user(db, user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    
    user_data = UserRead.model_validate(db_user).model_dump()
    return response(
        status_code=201,
        message="Usuario creado exitosamente",
        data=user_data
    )

# ✅ GET /users/me → DEBE IR ANTES que /{user_id}
@router.get("/me")
async def get_me_route(current_user: User = Depends(get_current_user)):
    # Valida con Pydantic y serializa:
    user_data = UserRead.model_validate(current_user).model_dump()
    return response(
        status_code=200,
        message="Perfil obtenido correctamente",
        data=user_data
    )

# ✅ GET /users/{user_id}
@router.get("/{user_id}")
async def get_user_route(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.administrador))
):
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail=f"Usuario con id {user_id} no encontrado")
    user_data = UserRead.model_validate(db_user).model_dump()
    return response(
        status_code=200,
        message="Usuario obtenido exitosamente",
        data=user_data
    )

# ✅ GET /users/ → listado, protegido si quieres
@router.get("/", response_model=UsersPaginatedResponse)
async def get_users_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, gt=0, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.administrador))
):
    users = get_users(db, skip, limit)
    total = get_users_count(db)

    users_data = [UserRead.model_validate(user).model_dump() for user in users]

    return response(
        status_code=200,
        message="Usuarios obtenidos exitosamente",
        data=users_data,
        count_data=total,
    )
@router.patch("/{user_id}/rol")
async def update_user_rol_route(
    user_id: UUID,
    update_data: UserUpdateRol,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.administrador))
):
    db_user = update_user_rol(db, user_id, update_data)
    if not db_user:
        raise HTTPException(status_code=404, detail=f"Usuario con id {user_id} no encontrado")

    user_data = UserRead.model_validate(db_user).model_dump()
    return response(
        status_code=200,
        message="Rol de usuario actualizado exitosamente",
        data=user_data
    )


@router.patch("/{user_id}/branch")
async def update_user_branch_route(
    user_id: UUID,
    update_data: UserUpdateBranch,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.administrador))
):
    try:
        db_user = update_user_branch(db, user_id, update_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not db_user:
        raise HTTPException(status_code=404, detail=f"Usuario con id {user_id} no encontrado")

    user_data = UserRead.model_validate(db_user).model_dump()
    return response(
        status_code=200,
        message="Sucursal de usuario actualizada exitosamente",
        data=user_data
    )
