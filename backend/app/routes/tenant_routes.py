from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum, TenantStatusEnum
from app.schemas.tenant_schema import TenantAdminCreate, TenantBrandingUpdate, TenantCreate, TenantStatusUpdate, TenantUpdate
from app.services.tenant_service import (
    NoTenantAdmin,
    create_tenant,
    open_tenant_panel,
    register_tenant_admin,
    get_branding,
    update_branding_color,
    update_tenant_logo,
    delete_tenant_logo,
    get_tenant,
    list_tenants,
    update_tenant,
    update_tenant_status,
)
from app.utils.response import response

router = APIRouter(prefix="/saas/tenants", tags=["SaaS Tenants"])
logger = logging.getLogger(__name__)


# [CU01 - Secuencia: Pasos 1.1, 3.15, 4.7, 6.11] TenantManagementPageComponent llama a list_tenants_route(skip, limit, search, status_filter) de tenant_routes (GET /api/saas/tenants/)
# [CU01 - Secuencia: Pasos 1.6, 3.20, 4.12, 6.16] tenant_routes retorna list_tenants_route(skip, limit, search, status_filter): 200 Empresas obtenidas exitosamente a TenantManagementPageComponent
@router.get("/")
async def list_tenants_route(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, gt=0, le=100),
    search: Optional[str] = Query(None, description="Buscar por nombre, slug o email"),
    status_filter: Optional[TenantStatusEnum] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.superadministrador)),
):
    tenants, total = list_tenants(
        db,
        skip=skip,
        limit=limit,
        search=search,
        status=status_filter,
    )
    return response(
        status_code=status.HTTP_200_OK,
        message="Empresas obtenidas exitosamente",
        data=tenants,
        count_data=total,
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_tenant_route(
    payload: TenantCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.superadministrador)),
):
    try:
        tenant = create_tenant(db, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return response(
        status_code=status.HTTP_201_CREATED,
        message="Empresa creada exitosamente",
        data=tenant,
    )


@router.get("/public")
async def list_public_tenants_route(db: Session = Depends(get_db)):
    tenants, total = list_tenants(
        db,
        skip=0,
        limit=100,
        status=TenantStatusEnum.active,
    )
    public_data = [
        {
            "id": str(t["id"]),
            "name": t["name"],
            "slug": t["slug"],
            "currency": t["currency"],
            "country": t["country"],
        }
        for t in tenants
    ]
    return response(
        status_code=status.HTTP_200_OK,
        message="Empresas y marcas obtenidas exitosamente",
        data=public_data,
        count_data=total,
    )


@router.get("/{tenant_id}")
async def get_tenant_route(
    tenant_id: UUID,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.superadministrador)),
):
    tenant = get_tenant(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empresa con id {tenant_id} no encontrada",
        )

    return response(
        status_code=status.HTTP_200_OK,
        message="Empresa obtenida exitosamente",
        data=tenant,
    )


# [CU01 - Secuencia: Paso 6.1] TenantManagementPageComponent llama a register_tenant_admin_route(tenant_id, payload) de tenant_routes (POST /api/saas/tenants/{tenant_id}/admin)
# [CU01 - Secuencia: Paso 6.10] tenant_routes retorna register_tenant_admin_route(tenant_id, payload): 201 Administrador registrado exitosamente a TenantManagementPageComponent
@router.post("/{tenant_id}/admin", status_code=status.HTTP_201_CREATED)
async def register_tenant_admin_route(
    tenant_id: UUID,
    payload: TenantAdminCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.superadministrador)),
):
    try:
        tenant = register_tenant_admin(db, tenant_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no encontrada")
    return response(status_code=status.HTTP_201_CREATED, message="Administrador registrado exitosamente", data=tenant)


# [CU01 - Secuencia: Paso 5.1] TenantManagementPageComponent llama a open_tenant_panel_route(tenant_id) de tenant_routes (POST /api/saas/tenants/{tenant_id}/panel-session)
# [CU01 - Secuencia: Paso 5.8] tenant_routes retorna open_tenant_panel_route(tenant_id): 200 Ingresaste al panel de ... a TenantManagementPageComponent
@router.post("/{tenant_id}/panel-session")
async def open_tenant_panel_route(
    tenant_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.superadministrador)),
):
    """The superadmin enters the company's administrative panel as its administrator."""
    try:
        session = open_tenant_panel(db, tenant_id, UUID(current_user["sub"]))
    except NoTenantAdmin as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no encontrada")
    logger.info("Superadmin %s entered the panel of tenant %s", current_user["sub"], tenant_id)
    return response(status_code=status.HTTP_200_OK, message=f"Ingresaste al panel de {session.pop('tenant_name')}", data=session)


# [CU26 - Secuencia: Pasos 1.1, 4.1] TenantBrandingEditorComponent llama a update_tenant_route(tenant_id, payload) de tenant_routes (PATCH /api/saas/tenants/{tenant_id})
# [CU26 - Secuencia: Pasos 1.6, 4.6] tenant_routes retorna update_tenant_route(tenant_id, payload): 200 Empresa actualizada exitosamente a TenantBrandingEditorComponent
@router.patch("/{tenant_id}")
async def update_tenant_route(
    tenant_id: UUID,
    payload: TenantUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.superadministrador)),
):
    try:
        tenant = update_tenant(db, tenant_id, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empresa con id {tenant_id} no encontrada",
        )

    return response(
        status_code=status.HTTP_200_OK,
        message="Empresa actualizada exitosamente",
        data=tenant,
    )


# [CU01 - Secuencia: Paso 4.1] TenantManagementPageComponent llama a update_tenant_status_route(tenant_id, payload) de tenant_routes (PATCH /api/saas/tenants/{tenant_id}/status)
# [CU01 - Secuencia: Paso 4.6] tenant_routes retorna update_tenant_status_route(tenant_id, payload): 200 Estado de empresa actualizado exitosamente a TenantManagementPageComponent
@router.patch("/{tenant_id}/status")
async def update_tenant_status_route(
    tenant_id: UUID,
    payload: TenantStatusUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.superadministrador)),
):
    tenant = update_tenant_status(db, tenant_id, payload.status)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empresa con id {tenant_id} no encontrada",
        )

    return response(
        status_code=status.HTTP_200_OK,
        message="Estado de empresa actualizado exitosamente",
        data=tenant,
    )



# --- CU1 branding: logo and color shown in the staff panel and on receipts ------------------------

async def _save_logo(db: Session, tenant_id: UUID, file: UploadFile) -> dict:
    try:
        branding = update_tenant_logo(db, tenant_id, await file.read(), file.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # Cloudinary unavailable or misconfigured
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="No se pudo subir el logo") from exc
    if branding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Empresa con id {tenant_id} no encontrada")
    return branding


# [CU26 - Secuencia: Pasos 1.13, 2.1, 3.1, 4.13] TenantBrandingEditorComponent llama a get_branding_route(tenant_id) de tenant_routes (GET /api/saas/tenants/{tenant_id}/branding)
# [CU26 - Secuencia: Pasos 1.18, 2.6, 3.6, 4.18] tenant_routes retorna get_branding_route(tenant_id): 200 Marca de la empresa obtenida a TenantBrandingEditorComponent
@router.get("/{tenant_id}/branding")
async def get_branding_route(tenant_id: UUID, db: Session = Depends(get_db)):
    branding = get_branding(db, tenant_id)
    if not branding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Empresa con id {tenant_id} no encontrada")
    return response(status_code=status.HTTP_200_OK, message="Marca de la empresa obtenida", data=branding)


# [CU26 - Secuencia: Pasos 1.7, 4.7] TenantBrandingEditorComponent llama a update_my_branding_route(payload) de tenant_routes (PUT /api/saas/tenants/me/branding)
# [CU26 - Secuencia: Pasos 1.12, 4.12] tenant_routes retorna update_my_branding_route(payload): 200 Marca de la empresa actualizada a TenantBrandingEditorComponent
@router.put("/me/branding")
async def update_my_branding_route(
    payload: TenantBrandingUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.administrador)),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    branding = update_branding_color(db, tenant_id, payload.primary_color)
    return response(status_code=status.HTTP_200_OK, message="Marca de la empresa actualizada", data=branding)


# [CU26 - Secuencia: Paso 2.7] TenantBrandingEditorComponent llama a upload_my_logo_route(file) de tenant_routes (POST /api/saas/tenants/me/logo)
# [CU26 - Secuencia: Paso 2.8] tenant_routes retorna upload_my_logo_route(file): 200 Logo de la empresa actualizado a TenantBrandingEditorComponent
@router.post("/me/logo")
async def upload_my_logo_route(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.administrador)),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    branding = await _save_logo(db, tenant_id, file)
    return response(status_code=status.HTTP_200_OK, message="Logo de la empresa actualizado", data=branding)


@router.post("/{tenant_id}/logo")
async def upload_tenant_logo_route(
    tenant_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.superadministrador)),
):
    branding = await _save_logo(db, tenant_id, file)
    return response(status_code=status.HTTP_200_OK, message="Logo de la empresa actualizado", data=branding)


# [CU26 - Secuencia: Paso 3.7] TenantBrandingEditorComponent llama a delete_my_logo_route() de tenant_routes (DELETE /api/saas/tenants/me/logo)
# [CU26 - Secuencia: Paso 3.12] tenant_routes retorna delete_my_logo_route(): 200 Logo de la empresa eliminado a TenantBrandingEditorComponent
@router.delete("/me/logo")
async def delete_my_logo_route(
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.administrador)),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    branding = delete_tenant_logo(db, tenant_id)
    if not branding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no encontrada")
    return response(status_code=status.HTTP_200_OK, message="Logo de la empresa eliminado", data=branding)


@router.delete("/{tenant_id}/logo")
async def delete_tenant_logo_route(
    tenant_id: UUID,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.superadministrador)),
):
    branding = delete_tenant_logo(db, tenant_id)
    if not branding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa no encontrada")
    return response(status_code=status.HTTP_200_OK, message="Logo de la empresa eliminado", data=branding)
