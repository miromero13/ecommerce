from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.models.provider import Provider
from app.models.user import User
from app.schemas.enums import RolEnum
from app.schemas.provider_schema import ProviderCreate, ProviderRead, ProviderStatusUpdate, ProviderUpdate
from app.schemas.provider_availability_schema import ProviderAvailabilityBatchUpdate
from app.services.provider_service import create_provider, get_providers, update_provider_status, update_provider_full, delete_provider, list_provider_products, provider_availability_map, update_provider_availability
from app.services.catalog_service import _product_to_read
from app.utils.response import response


router = APIRouter(prefix="/providers", tags=["Providers"])


def _provider_products_response(db: Session, provider_id: UUID):
    products = list_provider_products(db, provider_id)
    quantities = provider_availability_map(db, provider_id, [variant.id for product in products for variant in product.variants])
    return [_product_to_read(product, product.variants, provider_quantity_map=quantities) for product in products]


@router.get("/me/products")
async def list_my_products(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.proveedor)),
):
    provider = db.query(Provider).filter(Provider.user_id == UUID(current_user["sub"])).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return response(status_code=200, message="Productos del proveedor obtenidos exitosamente", data=_provider_products_response(db, provider.id))


@router.put("/me/availability")
async def update_my_availability(
    payload: ProviderAvailabilityBatchUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.proveedor)),
):
    provider = db.query(Provider).filter(Provider.user_id == UUID(current_user["sub"])).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    try:
        quantities = update_provider_availability(db, provider.id, payload.updates)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return response(status_code=200, message="Disponibilidad actualizada exitosamente", data=[{"variant_id": variant_id, "quantity": quantity} for variant_id, quantity in quantities.items()])


@router.get("/{provider_id}/products")
async def list_provider_products_route(
    provider_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return response(status_code=200, message="Productos del proveedor obtenidos exitosamente", data=_provider_products_response(db, provider_id))


@router.get("/")
async def list_providers_route(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    rows = get_providers(db)
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
                "status": provider.status,
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
):
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
            "status": db_provider.status,
        }
    ).model_dump()
    return response(status_code=status.HTTP_201_CREATED, message="Proveedor creado exitosamente", data=provider_data)


@router.patch("/{provider_id}/status")
async def update_provider_status_route(
    provider_id: UUID,
    update_data: ProviderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
):
    target_provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not target_provider:
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
            "status": db_provider.status,
        }
    ).model_dump()
    return response(status_code=status.HTTP_200_OK, message="Estado de proveedor actualizado exitosamente", data=provider_data)


@router.put("/{provider_id}")
async def update_provider_full_route(
    provider_id: UUID,
    update_data: ProviderUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
):
    target_provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not target_provider:
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
            "status": db_provider.status,
        }
    ).model_dump()
    return response(status_code=status.HTTP_200_OK, message="Proveedor actualizado exitosamente", data=provider_data)


@router.delete("/{provider_id}")
async def delete_provider_route(
    provider_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
):
    target_provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not target_provider:
        raise HTTPException(status_code=404, detail=f"Proveedor con id {provider_id} no encontrado")
    try:
        deleted = delete_provider(db, provider_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Proveedor con id {provider_id} no encontrado")

    return response(status_code=status.HTTP_200_OK, message="Proveedor eliminado exitosamente", data={"id": str(provider_id)})
