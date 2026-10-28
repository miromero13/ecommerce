from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.user_schema import UserCreate, UserRead, UserLogin, UserOut
from app.models.user import User
from app.core.database import get_db
from app.auth.hash import verify_password
from app.auth.jwt import create_access_token
from app.services.user_service import create_user
from app.utils.response import response


from app.services.rbac_service import effective_permissions


router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", summary="Registro de customer/cliente")
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = create_user(db, user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    perms = effective_permissions(db, db_user)
    access_token = create_access_token(
        data={
            "sub": str(db_user.id),
            "rol": db_user.rol.value,
            "tenant_id": str(db_user.tenant_id) if db_user.tenant_id else None,
            "branch_id": str(db_user.branch_id) if db_user.branch_id else None,
            "permissions": perms,
        }
    )

    user_data = UserRead.model_validate(db_user).model_dump()
    user_data["permissions"] = perms

    return response(
        status_code=status.HTTP_201_CREATED,
        message="Registro de customer/cliente exitoso",
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_data,
        },
    )

@router.post("/login", summary="Inicio de sesión unificado")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    normalized_email = user_data.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )
    if user_data.rol is not None and user.rol != user_data.rol:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no pertenece al rol solicitado",
        )
    perms = effective_permissions(db, user)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "rol": user.rol.value,
            "tenant_id": str(user.tenant_id) if user.tenant_id else None,
            "branch_id": str(user.branch_id) if user.branch_id else None,
            "permissions": perms,
        }
    )
    user_out = UserRead.model_validate(user).model_dump()
    user_out["permissions"] = perms
    return response(
        status_code=status.HTTP_200_OK,
        message="Inicio de sesión exitoso",
        data={"access_token": access_token, "token_type": "bearer", "user": user_out},
    )
