from __future__ import annotations

import datetime
from decimal import Decimal
import uuid
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.auth.dependencies import get_current_tenant_id, get_current_user, require_roles
from app.core.database import get_db
from app.models.category import Category
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.catalog_enums import ProductStatusEnum
from app.schemas.enums import RolEnum
from app.schemas.offline_schema import ConflictResolveRequest, OfflineQueueSyncRequest
from app.services import offline_sync_service
from app.utils.response import response

router = APIRouter(prefix="/offline", tags=["Offline POS"])
STAFF = (RolEnum.cajero, RolEnum.encargado, RolEnum.administrador)


# [CU23 - Secuencia: Paso 1.2] OfflineCatalogService llama a get_offline_catalog_sync(branch_id) de offline_routes (GET /api/offline/catalog-sync)
# [CU23 - Secuencia: Paso 1.11] offline_routes retorna get_offline_catalog_sync(branch_id): 200 Catálogo offline sincronizado exitosamente a OfflineCatalogService
@router.get("/catalog-sync")
def get_offline_catalog_sync(
    request: Request,
    branch_id: Optional[UUID] = Query(None, description="Sucursal para filtrar stock disponible"),
    db: Session = Depends(get_db),
):
    """
    CU23: Retorna el catálogo completo y liviano optimizado para almacenamiento
    local en IndexedDB (Web) y SQLite (Móvil). Incluye SKU, precios, talles,
    colores y stock disponible para operar sin conexión.
    """
    tenant_ref = getattr(request.state, "tenant_ref", None)
    tenant: Optional[Tenant] = None

    if tenant_ref:
        try:
            val = uuid.UUID(str(tenant_ref))
            # [CU23 - Secuencia: Pasos 1.3, 1.5] offline_routes ejecuta select(Tenant) sobre la entidad Empresa
            # [CU23 - Secuencia: Pasos 1.4, 1.6] Empresa retorna select(Tenant): Query[Tenant] a offline_routes
            tenant = db.scalars(select(Tenant).where(Tenant.id == val)).first()
        except (ValueError, AttributeError):
            tenant = db.scalars(select(Tenant).where(Tenant.slug == str(tenant_ref))).first()

    query = (
        # [CU23 - Secuencia: Paso 1.7] offline_routes ejecuta db.query(Product) sobre la entidad Producto
        # [CU23 - Secuencia: Paso 1.8] Producto retorna db.query(Product): Query[Product] a offline_routes
        db.query(Product)
        .options(
            selectinload(Product.variants).joinedload(ProductVariant.size),
            selectinload(Product.variants).joinedload(ProductVariant.color),
            selectinload(Product.variants).selectinload(ProductVariant.inventory),
        )
    )

    if tenant:
        query = query.filter(Product.tenant_id == tenant.id)

    products = query.all()
    # [CU23 - Secuencia: Paso 1.9] offline_routes ejecuta db.query(Category) sobre la entidad Categoria
    # [CU23 - Secuencia: Paso 1.10] Categoria retorna db.query(Category): list[Category] a offline_routes
    categories = {c.id: c.name for c in db.query(Category).all()}
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    catalog_items = []

    for product in products:
        active_variants = [
            v for v in product.variants
            if getattr(v, "status", None) == ProductStatusEnum.active or getattr(v, "status", None) is None
        ]
        if not active_variants:
            continue

        variants_data = []
        for variant in active_variants:
            if branch_id:
                branch_inv = next((inv for inv in variant.inventory if inv.branch_id == branch_id), None)
                available_stock = max(0, (branch_inv.quantity - branch_inv.reserved_quantity)) if branch_inv else 0
            else:
                available_stock = sum(max(0, inv.quantity - inv.reserved_quantity) for inv in variant.inventory)

            variants_data.append({
                "id": str(variant.id),
                "sku": variant.sku,
                "price": float(variant.price) if variant.price is not None else 0.0,
                "size": variant.size.name if variant.size else None,
                "size_id": str(variant.size_id) if variant.size_id else None,
                "color": variant.color.name if variant.color else None,
                "color_hex": variant.color.hex_code if variant.color else None,
                "color_id": str(variant.color_id) if variant.color_id else None,
                "image_url": variant.image_url,
                "available_stock": available_stock,
            })

        catalog_items.append({
            "id": str(product.id),
            "tenant_id": str(product.tenant_id),
            "name": product.name,
            "description": product.description or "",
            "category_id": str(product.category_id) if product.category_id else None,
            "category": categories.get(product.category_id, "General"),
            "discount_type": product.discount_type,
            "discount_value": float(product.discount_value) if product.discount_value is not None else None,
            "variants": variants_data,
            "synced_at": now_iso,
        })

    return response(
        status_code=200,
        message="Catálogo offline sincronizado exitosamente",
        data={
            "branch_id": str(branch_id) if branch_id else None,
            "total_products": len(catalog_items),
            "synced_at": now_iso,
            "products": catalog_items,
        },
    )


# [CU30 - Secuencia: Pasos 1.5, 2.5] OfflineQueueService llama a sync_offline_queue(payload) de offline_routes (POST /api/offline/queue-sync)
# [CU30 - Secuencia: Pasos 1.24, 2.24] offline_routes retorna sync_offline_queue(payload): 200 Lote procesado: ... sincronizadas, ... conflictos. a OfflineQueueService
@router.post("/queue-sync")
def sync_offline_queue(
    payload: OfflineQueueSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant_id: UUID | None = Depends(get_current_tenant_id),
    _: dict = Depends(require_roles(RolEnum.cajero)),
):
    """CU30: confirms each offline cash sale (first to arrive keeps the stock) or records it as a conflict."""
    if current_user.branch_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="branch_id es requerido")
    result = offline_sync_service.sync_batch(db, current_user, current_tenant_id, current_user.branch_id,
                                             payload.operations)
    return response(
        status_code=200,
        message=f"Lote procesado: {result['synced_count']} sincronizadas, {result['conflicts_count']} conflictos.",
        data=result,
    )


@router.get("/conflicts")
def list_offline_conflicts(
    status_filter: str = Query("pending", alias="status", pattern="^(pending|resolved|all)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant_id: UUID | None = Depends(get_current_tenant_id),
    _: dict = Depends(require_roles(*STAFF)),
):
    """CU30: conflicts of the branch (company-wide for the admin) and the cash still owed to customers."""
    data = offline_sync_service.list_conflicts(db, current_user, current_tenant_id, status_filter)
    return response(status_code=200, message="Conflictos offline obtenidos exitosamente", data=data)


RESOLUTION_MESSAGES = {
    "cash_refund": "Conflicto resuelto: efectivo devuelto al cliente y registrado como retiro de caja.",
    "wallet_credit": "Conflicto resuelto: saldo acreditado en la billetera del cliente con 10 % de bonificación.",
    "exchange": "Conflicto resuelto: la prenda se cambió por otra disponible.",
    "delivered": "Conflicto resuelto: la venta se mantiene y se registró el ajuste de inventario.",
}


# [CU30 - Secuencia: Pasos 4.2, 5.2] OfflineSyncService llama a resolve_offline_conflict(conflict_id, payload) de offline_routes (POST /api/offline/conflicts/{conflict_id}/resolve)
# [CU30 - Secuencia: Pasos 4.13, 5.13] offline_routes retorna resolve_offline_conflict(conflict_id, payload): 200 Conflicto resuelto a OfflineSyncService
@router.post("/conflicts/{conflict_id}/resolve")
def resolve_offline_conflict(
    conflict_id: UUID,
    payload: ConflictResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    current_tenant_id: UUID | None = Depends(get_current_tenant_id),
    _: dict = Depends(require_roles(*STAFF)),
):
    """CU30: resolves a conflict once: cash refund, wallet credit (+10 %), exchange or delivered."""
    try:
        data = offline_sync_service.resolve_conflict(db, current_user, current_tenant_id, conflict_id, payload)
    except offline_sync_service.ConflictStateError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=200, message=RESOLUTION_MESSAGES[payload.action], data=data)
