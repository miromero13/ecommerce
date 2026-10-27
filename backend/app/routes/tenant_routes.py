from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum, TenantStatusEnum
from app.schemas.tenant_schema import TenantBrandingUpdate, TenantCreate, TenantStatusUpdate, TenantUpdate
from app.services.tenant_service import (
    create_tenant,
    get_branding,
    update_branding_color,
    update_tenant_logo,
    get_tenant,
    list_tenants,
    update_tenant,
    update_tenant_status,
)
from app.utils.response import response

router = APIRouter(prefix="/saas/tenants", tags=["SaaS Tenants"])


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


@router.get("/{tenant_id}/branding")
async def get_branding_route(tenant_id: UUID, db: Session = Depends(get_db)):
    branding = get_branding(db, tenant_id)
    if not branding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Empresa con id {tenant_id} no encontrada")
    return response(status_code=status.HTTP_200_OK, message="Marca de la empresa obtenida", data=branding)


@router.put("/me/branding")
async def update_my_branding_route(
    payload: TenantBrandingUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.administrador)),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    branding = update_branding_color(db, tenant_id, payload.primary_color)
    return response(status_code=status.HTTP_200_OK, message="Marca de la empresa actualizada", data=branding)


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
