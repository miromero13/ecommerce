from __future__ import annotations

import datetime
import uuid
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import get_db
from app.models.category import Category
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.tenant import Tenant
from app.schemas.catalog_enums import ProductStatusEnum
from app.utils.response import response

router = APIRouter(prefix="/offline", tags=["Offline POS"])


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
            tenant = db.scalars(select(Tenant).where(Tenant.id == val)).first()
        except (ValueError, AttributeError):
            tenant = db.scalars(select(Tenant).where(Tenant.slug == str(tenant_ref))).first()

    # Query products with categories and variants
    query = (
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

    # Cache categories for quick name lookup
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
            # Calculate stock according to branch if specified, or total available
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
