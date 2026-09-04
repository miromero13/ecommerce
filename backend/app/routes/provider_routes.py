from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.auth.dependencies import require_roles
from app.auth.dependencies import get_current_branch_id
from app.core.database import get_db
from app.models.provider import Provider
from app.models.user import User
from app.schemas.enums import RolEnum
from app.schemas.provider_schema import ProviderCreate, ProviderRead, ProviderStatusUpdate, ProviderUpdate, ProviderActiveUpdate
from app.services.provider_service import create_provider, get_providers, update_provider_status, update_provider_full, delete_provider, set_provider_active
from app.utils.response import response


router = APIRouter(prefix="/providers", tags=["Providers"])


@router.get("/")
async def list_providers_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
):
    rows = get_providers(db, current_branch_id)
    providers_data = [
        ProviderRead.model_validate(
            {
                "id": provider.id,
                "user_id": provider.user_id,
                "business_name": provider.business_name,
                "contact_name": provider.contact_name,
                "email": user.email,
                "gender": user.gender,
                "phone": provider.phone,
                "branch_id": provider.branch_id,
                "status": provider.status,
                "is_active": provider.is_active,
            }
        ).model_dump()
        for provider, user in rows
    ]
    return response(status_code=status.HTTP_200_OK, message="Proveedores obtenidos exitosamente", data=providers_data)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_provider_route(
    provider: ProviderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
):
    if current_branch_id is not None and provider.branch_id not in {None, current_branch_id}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No puedes crear proveedores en otra sucursal")

    if current_branch_id is not None and provider.branch_id is None:
        provider = provider.model_copy(update={"branch_id": current_branch_id})

    try:
        db_provider = create_provider(db, provider)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    user = db.query(User).filter(User.id == db_provider.user_id).first()
    provider_data = ProviderRead.model_validate(
        {
            "id": db_provider.id,
            "user_id": db_provider.user_id,
            "business_name": db_provider.business_name,
            "contact_name": db_provider.contact_name,
            "email": user.email if user else provider.email,
            "gender": user.gender if user else provider.gender,
            "phone": db_provider.phone,
            "branch_id": db_provider.branch_id,
            "status": db_provider.status,
            "is_active": db_provider.is_active,
        }
    ).model_dump()
    return response(status_code=status.HTTP_201_CREATED, message="Proveedor creado exitosamente", data=provider_data)


@router.patch("/{provider_id}/status")
async def update_provider_status_route(
    provider_id: UUID,
    update_data: ProviderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
):
    target_provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not target_provider:
        raise HTTPException(status_code=404, detail=f"Proveedor con id {provider_id} no encontrado")
    if current_branch_id is not None and target_provider.branch_id != current_branch_id:
        raise HTTPException(status_code=404, detail=f"Proveedor con id {provider_id} no encontrado")

    db_provider = update_provider_status(db, provider_id, update_data)
    if not db_provider:
        raise HTTPException(status_code=404, detail=f"Proveedor con id {provider_id} no encontrado")

    user = db.query(User).filter(User.id == db_provider.user_id).first()
    provider_data = ProviderRead.model_validate(
        {
            "id": db_provider.id,
            "user_id": db_provider.user_id,
            "business_name": db_provider.business_name,
            "contact_name": db_provider.contact_name,
            "email": user.email if user else "",
            "gender": user.gender if user else "masculino",
            "phone": db_provider.phone,
            "branch_id": db_provider.branch_id,
            "status": db_provider.status,
            "is_active": db_provider.is_active,
        }
    ).model_dump()
    return response(status_code=status.HTTP_200_OK, message="Estado de proveedor actualizado exitosamente", data=provider_data)


@router.put("/{provider_id}")
async def update_provider_full_route(
    provider_id: UUID,
    update_data: ProviderUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
):
    target_provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not target_provider:
        raise HTTPException(status_code=404, detail=f"Proveedor con id {provider_id} no encontrado")
    if current_branch_id is not None and target_provider.branch_id != current_branch_id:
        raise HTTPException(status_code=404, detail=f"Proveedor con id {provider_id} no encontrado")

    try:
        db_provider = update_provider_full(db, provider_id, update_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not db_provider:
        raise HTTPException(status_code=404, detail=f"Proveedor con id {provider_id} no encontrado")

    user = db.query(User).filter(User.id == db_provider.user_id).first()
    provider_data = ProviderRead.model_validate(
        {
            "id": db_provider.id,
            "user_id": db_provider.user_id,
            "business_name": db_provider.business_name,
            "contact_name": db_provider.contact_name,
            "email": user.email if user else "",
            "gender": user.gender if user else "masculino",
            "phone": db_provider.phone,
            "branch_id": db_provider.branch_id,
            "status": db_provider.status,
            "is_active": db_provider.is_active,
        }
    ).model_dump()
    return response(status_code=status.HTTP_200_OK, message="Proveedor actualizado exitosamente", data=provider_data)


@router.patch("/{provider_id}/active")
async def update_provider_active_route(
    provider_id: UUID,
    update_data: ProviderActiveUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
):
    target_provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not target_provider:
        raise HTTPException(status_code=404, detail=f"Proveedor con id {provider_id} no encontrado")
    if current_branch_id is not None and target_provider.branch_id != current_branch_id:
        raise HTTPException(status_code=404, detail=f"Proveedor con id {provider_id} no encontrado")

    db_provider = set_provider_active(db, provider_id, update_data.is_active)
    if not db_provider:
        raise HTTPException(status_code=404, detail=f"Proveedor con id {provider_id} no encontrado")

    user = db.query(User).filter(User.id == db_provider.user_id).first()
    provider_data = ProviderRead.model_validate(
        {
            "id": db_provider.id,
            "user_id": db_provider.user_id,
            "business_name": db_provider.business_name,
            "contact_name": db_provider.contact_name,
            "email": user.email if user else "",
            "gender": user.gender if user else "masculino",
            "phone": db_provider.phone,
            "branch_id": db_provider.branch_id,
            "status": db_provider.status,
            "is_active": db_provider.is_active,
        }
    ).model_dump()
    return response(status_code=status.HTTP_200_OK, message="Estado de proveedor actualizado exitosamente", data=provider_data)


@router.delete("/{provider_id}")
async def delete_provider_route(
    provider_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
    current_branch_id: UUID | None = Depends(get_current_branch_id),
):
    target_provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not target_provider:
        raise HTTPException(status_code=404, detail=f"Proveedor con id {provider_id} no encontrado")
    if current_branch_id is not None and target_provider.branch_id != current_branch_id:
        raise HTTPException(status_code=404, detail=f"Proveedor con id {provider_id} no encontrado")

    try:
        deleted = delete_provider(db, provider_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Proveedor con id {provider_id} no encontrado")

    return response(status_code=status.HTTP_200_OK, message="Proveedor eliminado exitosamente", data={"id": str(provider_id)})
