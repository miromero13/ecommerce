from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    get_current_tenant_id,
    get_current_user,
    require_permission,
)
from app.core.database import get_db
from app.models.user import User
from app.schemas.enums import RolEnum
from app.schemas.rbac_schema import (
    PermissionRead,
    RoleCreate,
    RoleRead,
    RoleUpdate,
    UserRolesAssign,
)
from app.services.rbac_service import (
    assign_user_roles,
    create_role,
    list_permissions,
    list_roles,
    update_role,
)
from app.utils.response import response

router = APIRouter(prefix="/rbac", tags=["RBAC"])


@router.get("/permissions", summary="Obtener catálogo de permisos")
def get_permissions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("rbac:manage")),
):
    perms = list_permissions(db)
    data = [PermissionRead.model_validate(p).model_dump() for p in perms]
    return response(
        status_code=status.HTTP_200_OK,
        message="Catálogo de permisos obtenido",
        data=data,
    )


@router.get("/roles", summary="Listar roles de la organización")
def get_roles(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    current_user: dict = Depends(require_permission("rbac:manage")),
):
    tenant_id = user.tenant_id
    roles = list_roles(db, tenant_id=tenant_id)
    data = [RoleRead.model_validate(r).model_dump() for r in roles]
    return response(
        status_code=status.HTTP_200_OK,
        message="Listado de roles obtenido",
        data=data,
    )


@router.post("/roles", summary="Crear un rol personalizado", status_code=status.HTTP_201_CREATED)
def post_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    current_user: dict = Depends(require_permission("rbac:manage")),
):
    tenant_id = user.tenant_id
    if not tenant_id and user.rol != RolEnum.superadministrador:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Se requiere una organización para crear roles personalizados",
        )
    role = create_role(db, tenant_id=tenant_id, data=payload)
    return response(
        status_code=status.HTTP_201_CREATED,
        message="Rol creado exitosamente",
        data=RoleRead.model_validate(role).model_dump(),
    )


@router.put("/roles/{role_id}", summary="Actualizar un rol personalizado")
def put_role(
    role_id: UUID,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    current_user: dict = Depends(require_permission("rbac:manage")),
):
    tenant_id = user.tenant_id
    role = update_role(db, tenant_id=tenant_id, role_id=role_id, data=payload)
    return response(
        status_code=status.HTTP_200_OK,
        message="Rol actualizado exitosamente",
        data=RoleRead.model_validate(role).model_dump(),
    )


@router.post("/users/{user_id}/roles", summary="Asignar roles personalizados a un usuario")
def assign_roles(
    user_id: UUID,
    payload: UserRolesAssign,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    current_user: dict = Depends(require_permission("rbac:manage")),
):
    tenant_id = user.tenant_id
    assigned = assign_user_roles(
        db,
        current_tenant_id=tenant_id,
        user_id=user_id,
        data=payload,
    )
    data = [RoleRead.model_validate(r).model_dump() for r in assigned]
    return response(
        status_code=status.HTTP_200_OK,
        message="Roles asignados al usuario exitosamente",
        data=data,
    )
