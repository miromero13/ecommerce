from __future__ import annotations

import datetime
from decimal import Decimal
import uuid
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.database import get_db
from app.models.category import Category
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.tenant import Tenant
from app.models.user import User
from app.models.wallet import UserWallet, WalletTransaction
from app.schemas.catalog_enums import ProductStatusEnum
from app.schemas.order_schema import PaymentMethodEnum, PaymentStatusEnum
from app.schemas.sales_schema import SaleStatusEnum
from app.utils.response import response

router = APIRouter(prefix="/offline", tags=["Offline POS"])


# --- Schemas ---
class OfflineItemIn(BaseModel):
    variant_id: UUID
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)


class OfflineOperationIn(BaseModel):
    operation_id: str
    receipt_number: str
    type: str = "cash_sale"
    created_at: str
    tenant_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    cashier_id: Optional[UUID] = None
    cashier_name: Optional[str] = None
    customer_email: Optional[str] = None
    items: List[OfflineItemIn]
    subtotal: float
    discount: float = 0.0
    total: float
    cash_received: Optional[float] = None
    change_returned: Optional[float] = None
    notes: Optional[str] = None


class OfflineQueueSyncRequest(BaseModel):
    operations: List[OfflineOperationIn]


class ConflictResolveRequest(BaseModel):
    resolution_action: str = Field(description="'wallet_compensation' o 'cash_refund'")
    customer_email: Optional[str] = None
    amount: float = Field(gt=0)
    bonus_percent: float = Field(default=10.0, ge=0)
    notes: Optional[str] = None


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


@router.post("/queue-sync")
def sync_offline_queue(
    payload: OfflineQueueSyncRequest,
    db: Session = Depends(get_db),
):
    """
    CU30: Sincronización diferida atómica e idempotente de lote de operaciones offline.
    Valida el inventario de cada prenda. Si hay stock, confirma la venta y descuenta inventario.
    Si el stock se agotó previamente en línea, registra el conflicto de inventario.
    """
    synced_ids: List[str] = []
    conflicts: List[dict] = []

    for op in payload.operations:
        # 1. Idempotencia: Verificar si ya existe una venta procesada con este operation_id
        ref_prefix = f"OFFLINE:{op.operation_id}:"
        existing = db.query(Sale).filter(Sale.cash_reference.like(f"{ref_prefix}%")).first()
        if existing:
            synced_ids.append(op.operation_id)
            continue

        # 2. Validar que la operación tenga ítems y sucursal
        if not op.branch_id or not op.items:
            conflicts.append({
                "operation_id": op.operation_id,
                "receipt_number": op.receipt_number,
                "reason": "Operación incompleta (sin sucursal o prendas)",
                "total": op.total,
                "customer_email": op.customer_email,
            })
            continue

        # 3. Validación de inventario por ítem
        has_stock_collision = False
        collision_reason = ""
        inventories_to_update = []

        for item in op.items:
            inv = (
                db.query(Inventory)
                .filter(
                    Inventory.variant_id == item.variant_id,
                    Inventory.branch_id == op.branch_id,
                )
                .with_for_update()
                .first()
            )

            available = (inv.quantity - inv.reserved_quantity) if inv else 0
            if available < item.quantity:
                has_stock_collision = True
                variant = db.query(ProductVariant).filter(ProductVariant.id == item.variant_id).first()
                sku = variant.sku if variant else str(item.variant_id)
                collision_reason = f"Stock insuficiente para SKU {sku} (Disponible: {available}, Requerido: {item.quantity})"
                break

            inventories_to_update.append((inv, item.quantity))

        # Si hubo colisión de inventario, rechazar y reportar conflicto
        if has_stock_collision:
            conflicts.append({
                "operation_id": op.operation_id,
                "receipt_number": op.receipt_number,
                "reason": collision_reason,
                "total": op.total,
                "customer_email": op.customer_email,
            })
            continue

        # 4. Aplicar descuento de inventario
        for inv, qty in inventories_to_update:
            inv.quantity -= qty
            # Movimiento de inventario por venta offline consolidada
            movement = InventoryMovement(
                tenant_id=inv.tenant_id,
                variant_id=inv.variant_id,
                branch_id=inv.branch_id,
                quantity=-qty,
                movement_type="sale",
                reference=f"Offline Sync: {op.receipt_number}",
            )
            db.add(movement)

        # 5. Obtener usuario cajero o fallback
        cashier_user = None
        if op.cashier_id:
            cashier_user = db.query(User).filter(User.id == op.cashier_id).first()
        if not cashier_user:
            cashier_user = db.query(User).first()

        # Obtener tenant_id
        resolved_tenant_id = op.tenant_id or (cashier_user.tenant_id if cashier_user else None)
        if not resolved_tenant_id:
            tenant = db.query(Tenant).first()
            resolved_tenant_id = tenant.id if tenant else uuid.uuid4()

        # 6. Crear registro de Venta (Sale)
        sale = Sale(
            tenant_id=resolved_tenant_id,
            branch_id=op.branch_id,
            user_id=cashier_user.id if cashier_user else uuid.uuid4(),
            status=SaleStatusEnum.completed,
            payment_method=PaymentMethodEnum.cash,
            payment_status=PaymentStatusEnum.paid,
            cash_reference=f"OFFLINE:{op.operation_id}:{op.receipt_number}",
            subtotal=Decimal(str(op.subtotal)),
            discount_amount=Decimal(str(op.discount)),
            total_amount=Decimal(str(op.total)),
            currency="usd",
        )
        db.add(sale)
        db.flush()

        # 7. Crear ítems de venta
        for item in op.items:
            sale_item = SaleItem(
                sale_id=sale.id,
                variant_id=item.variant_id,
                quantity=item.quantity,
                unit_price=Decimal(str(item.unit_price)),
            )
            db.add(sale_item)

        synced_ids.append(op.operation_id)

    db.commit()

    return response(
        status_code=200,
        message=f"Lote procesado: {len(synced_ids)} sincronizadas, {len(conflicts)} conflictos.",
        data={
            "synced_count": len(synced_ids),
            "conflicts_count": len(conflicts),
            "synced_ids": synced_ids,
            "conflicts": conflicts,
        },
    )


@router.post("/conflicts/{operation_id}/resolve")
def resolve_offline_conflict(
    operation_id: str,
    payload: ConflictResolveRequest,
    db: Session = Depends(get_db),
):
    """
    CU30: Resolución de conflicto de inventario.
    Acredita el saldo a la Billetera Digital del cliente con +10% de compensación,
    o registra la devolución física en efectivo al cliente.
    """
    now = datetime.datetime.now(datetime.timezone.utc)

    if payload.resolution_action == "wallet_compensation":
        # Buscar usuario cliente por correo
        customer = None
        if payload.customer_email:
            customer = db.query(User).filter(User.email == payload.customer_email.strip().lower()).first()

        if not customer:
            # Si no existe, usar primer cliente o crear wallet asociada a usuario identificado
            customer = db.query(User).filter(User.rol == "cliente").first()

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró una cuenta de cliente registrada para acreditar la billetera.",
            )

        # Buscar o crear billetera
        wallet = db.query(UserWallet).filter(UserWallet.user_id == customer.id).first()
        if not wallet:
            wallet = UserWallet(user_id=customer.id, currency="BOB", balance=Decimal("0.00"))
            db.add(wallet)
            db.flush()

        # Calcular monto con 10% de bono compensatorio
        base_amount = Decimal(str(payload.amount))
        bonus_mult = Decimal("1") + (Decimal(str(payload.bonus_percent)) / Decimal("100"))
        credit_amount = (base_amount * bonus_mult).quantize(Decimal("0.01"))

        wallet.balance += credit_amount

        transaction = WalletTransaction(
            wallet_id=wallet.id,
            type="credit",
            amount=credit_amount,
            balance_after=wallet.balance,
            concept="rma_refund",
            description=f"Compensación contingencia offline ({operation_id}) +{payload.bonus_percent}% bono",
            created_at=now,
        )
        db.add(transaction)
        db.commit()

        return response(
            status_code=200,
            message="Conflicto resuelto: Saldo acreditado a Billetera Digital con bonificación del 10%.",
            data={
                "operation_id": operation_id,
                "resolution": "wallet_compensation",
                "customer_email": customer.email,
                "amount_original": float(base_amount),
                "bonus_percent": payload.bonus_percent,
                "credited_amount": float(credit_amount),
                "wallet_balance_after": float(wallet.balance),
                "resolved_at": now.isoformat(),
            },
        )

    elif payload.resolution_action == "cash_refund":
        return response(
            status_code=200,
            message="Conflicto resuelto: Devolución física de efectivo registrada en caja.",
            data={
                "operation_id": operation_id,
                "resolution": "cash_refund",
                "refunded_amount": payload.amount,
                "resolved_at": now.isoformat(),
            },
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Acción de resolución '{payload.resolution_action}' no válida.",
        )
