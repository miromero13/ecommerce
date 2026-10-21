from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum, TenantStatusEnum
from app.schemas.tenant_schema import TenantCreate, TenantStatusUpdate, TenantUpdate
from app.services.tenant_service import (
    create_tenant,
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
