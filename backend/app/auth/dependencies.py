from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Callable
from uuid import UUID  # Si usas UUID
from app.core.database import get_db
from app.auth.jwt import decode_access_token
from app.models.user import User
from app.models.branch import Branch
from app.models.tenant import Tenant
from app.schemas.enums import RolEnum, TenantStatusEnum

security = HTTPBearer()  # Simple Bearer auth

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    try:
        user_uuid = UUID(user_id)
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )
    if user.rol not in [RolEnum.cliente, RolEnum.superadministrador]:
        if user.tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario sin empresa asociada",
            )
        tenant_status = db.query(Tenant.status).filter(Tenant.id == user.tenant_id).scalar()
        if tenant_status == TenantStatusEnum.suspended:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="La empresa está suspendida. Contactá al administrador de la plataforma.",
            )
        if user.rol in [RolEnum.encargado, RolEnum.cajero, RolEnum.delivery]:
            if user.branch_id is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Usuario operativo sin sucursal asignada",
                )
            branch = db.query(Branch).filter(
                Branch.id == user.branch_id,
                Branch.tenant_id == user.tenant_id,
                Branch.is_active.is_(True),
            ).first()
            if branch is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="La sucursal no existe o está inactiva en esta empresa",
                )
    return user


def get_current_payload(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user: User = Depends(get_current_user),
):
    # Keep other signed claims, but never authorize using historical assignments.
    # FastAPI caches get_current_user across role/scope/profile dependencies.
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )
    return {
        **payload,
        "sub": str(user.id),
        "rol": user.rol.value,
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "branch_id": str(user.branch_id) if user.branch_id else None,
    }


def require_roles(*allowed_roles: RolEnum) -> Callable:
    def role_dependency(
        payload: dict = Depends(get_current_payload),
    ) -> dict:
        if payload.get("rol") not in [role.value for role in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para acceder a este recurso",
            )
        return payload

    return role_dependency


def get_current_branch_id(payload: dict = Depends(get_current_payload)) -> UUID | None:
    if payload.get("rol") in [RolEnum.administrador.value, RolEnum.superadministrador.value, RolEnum.cliente.value]:
        return None

    branch_id = payload.get("branch_id")
    if not branch_id:
        return None

    return UUID(branch_id)


def get_current_tenant_id(payload: dict = Depends(get_current_payload)) -> UUID | None:
    rol = payload.get("rol")
    tenant_id_str = payload.get("tenant_id")
    if rol in [RolEnum.superadministrador.value, RolEnum.cliente.value]:
        return UUID(tenant_id_str) if tenant_id_str else None

    if not tenant_id_str:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario sin empresa asociada",
        )
    return UUID(tenant_id_str)


def get_tenant_and_branch_scope(
    payload: dict = Depends(get_current_payload),
) -> tuple[UUID | None, UUID | None]:
    """
    Retorna (tenant_id, branch_id) para consultas jerárquicas:
    1. Si el usuario tiene branch_id (cajero, encargado, delivery):
       retorna (tenant_id, branch_id) -> filtra estrictamente por ambos.
    2. Si solo tiene tenant_id (administrador, proveedor):
       retorna (tenant_id, None) -> filtra por empresa completa (consolidado).
    3. Si es superadministrador o cliente:
       retorna (None, None) -> visión global sin restricción obligatoria.
    """
    rol = payload.get("rol")
    tenant_id_str = payload.get("tenant_id")
    branch_id_str = payload.get("branch_id")
    tenant_id = UUID(tenant_id_str) if tenant_id_str else None
    branch_id = UUID(branch_id_str) if branch_id_str else None

    if rol in [RolEnum.superadministrador.value, RolEnum.cliente.value]:
        return (None, None)

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario sin empresa asociada",
        )

    if rol in [RolEnum.cajero.value, RolEnum.encargado.value, RolEnum.delivery.value]:
        if not branch_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario operativo sin sucursal asignada",
            )
        return (tenant_id, branch_id)

    # Administrador o proveedor (gobierno a nivel empresa)
    return (tenant_id, None)


def validate_tenant_access(
    resource_tenant_id: UUID | None,
    current_tenant_id: UUID | None,
) -> None:
    """Garantiza que un empleado de Empresa A no pueda ver ni mutar recursos de Empresa B."""
    if current_tenant_id is not None and resource_tenant_id != current_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenés permisos para acceder a los datos de esta empresa",
        )
