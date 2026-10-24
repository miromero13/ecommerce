from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.branch import Branch
from app.models.color import Color
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.provider import Provider
from app.models.provider_variant_availability import ProviderVariantAvailability
from app.models.replenishment_request import ReplenishmentRequest
from app.models.replenishment_request_item import ReplenishmentRequestItem
from app.models.size import Size
from app.schemas.enums import ProviderStatusEnum, RolEnum
from app.schemas.inventory_schema import InventoryMovementTypeEnum
from app.schemas.replenishment_schema import ReplenishmentRequestCreate, ReplenishmentStatusEnum
from app.services.inventory_service import _get_or_create_inventory

TRANSITIONS = {
    ReplenishmentStatusEnum.requested: ReplenishmentStatusEnum.accepted,
    ReplenishmentStatusEnum.accepted: ReplenishmentStatusEnum.preparing,
    ReplenishmentStatusEnum.preparing: ReplenishmentStatusEnum.awaiting_receipt,
}


def validate_transition(current: ReplenishmentStatusEnum, next_status: ReplenishmentStatusEnum, role: str, owns_provider: bool = False, owns_branch: bool = False) -> None:
    if next_status == ReplenishmentStatusEnum.delivered:
        if current != ReplenishmentStatusEnum.awaiting_receipt:
            raise ValueError("La solicitud no está pendiente de recepción")
        if role not in {RolEnum.administrador.value, RolEnum.encargado.value} or role == RolEnum.encargado.value and not owns_branch:
            raise PermissionError("No tienes permisos para confirmar la recepción")
        return
    if role != RolEnum.proveedor.value or not owns_provider:
        raise PermissionError("No tienes permisos para esta transición")
    if TRANSITIONS.get(current) != next_status:
        raise ValueError("Transición no permitida")


def _validate_references(db: Session, provider_id, branch_id, variant_ids, tenant_id):
    provider = db.query(Provider).filter(
        Provider.id == provider_id, Provider.tenant_id == tenant_id,
        Provider.status == ProviderStatusEnum.active,
    ).first()
    if not provider:
        raise ValueError("El proveedor no existe o no está activo")
    if not db.query(Branch).filter(
        Branch.id == branch_id, Branch.tenant_id == tenant_id, Branch.is_active.is_(True),
    ).first():
        raise ValueError("La sucursal de destino no existe o está inactiva")
    if len(set(variant_ids)) != len(variant_ids):
        raise ValueError("No puedes repetir variantes en una solicitud")
    assigned = db.query(ProductVariant.id).join(Product).filter(
        Product.provider_id == provider.id, Product.tenant_id == tenant_id,
        ProductVariant.tenant_id == tenant_id, ProductVariant.id.in_(variant_ids),
    ).all()
    if len(assigned) != len(variant_ids):
        raise ValueError("La variante no está asignada a este proveedor")


def create_request(db: Session, payload: ReplenishmentRequestCreate, requested_by: UUID, *, tenant_id):
    try:
        _validate_references(db, payload.provider_id, payload.branch_id,
                             [item.variant_id for item in payload.items], tenant_id)
        request = ReplenishmentRequest(tenant_id=tenant_id, provider_id=payload.provider_id,
                                       branch_id=payload.branch_id, requested_by=requested_by)
        request.items = [ReplenishmentRequestItem(variant_id=item.variant_id, requested_quantity=item.requested_quantity) for item in payload.items]
        db.add(request)
        db.commit()
        db.refresh(request)
        return request
    except Exception:
        db.rollback()
        raise


def _provider_id(db: Session, user_id, tenant_id):
    return db.query(Provider.id).filter(Provider.user_id == user_id, Provider.tenant_id == tenant_id).scalar()


def list_requests(db: Session, role: str, user_id: UUID, branch_id: UUID | None = None, *, tenant_id):
    query = db.query(ReplenishmentRequest).options(
        joinedload(ReplenishmentRequest.items).joinedload(ReplenishmentRequestItem.variant).joinedload(ProductVariant.product)
    ).filter(ReplenishmentRequest.tenant_id == tenant_id)
    if role == RolEnum.proveedor.value:
        provider_id = _provider_id(db, user_id, tenant_id)
        query = query.filter(ReplenishmentRequest.provider_id == provider_id) if provider_id else query.filter(False)
    elif role == RolEnum.encargado.value:
        query = query.filter(ReplenishmentRequest.branch_id == branch_id)
    return query.order_by(ReplenishmentRequest.created_at.desc()).all()


def _read_request(db: Session, request: ReplenishmentRequest):
    variant_ids = [item.variant_id for item in request.items]
    availability = {row.variant_id: row.quantity for row in db.query(ProviderVariantAvailability).filter(ProviderVariantAvailability.provider_id == request.provider_id, ProviderVariantAvailability.variant_id.in_(variant_ids)).all()} if variant_ids else {}
    return {
        "id": request.id, "provider_id": request.provider_id, "branch_id": request.branch_id, "requested_by": request.requested_by,
        "status": request.status, "created_at": request.created_at, "updated_at": request.updated_at,
        "delivered_by": request.delivered_by, "delivered_at": request.delivered_at,
        "items": [{
            "variant_id": item.variant_id, "product_name": item.variant.product.name, "sku": item.variant.sku,
            "size_name": db.query(Size.name).filter(Size.id == item.variant.size_id).scalar(),
            "color_name": db.query(Color.name).filter(Color.id == item.variant.color_id).scalar(),
            "provider_quantity": availability.get(item.variant_id, 0), "requested_quantity": item.requested_quantity,
        } for item in request.items],
    }


def serialize_requests(db: Session, requests):
    return [_read_request(db, request) for request in requests]


def transition_request(db: Session, request_id: UUID, next_status: ReplenishmentStatusEnum, role: str, user_id: UUID, branch_id: UUID | None, *, tenant_id):
    request = db.query(ReplenishmentRequest).options(selectinload(ReplenishmentRequest.items)).filter(
        ReplenishmentRequest.id == request_id, ReplenishmentRequest.tenant_id == tenant_id,
    ).with_for_update().first()
    if not request:
        raise LookupError("Solicitud no encontrada")
    if role == RolEnum.proveedor.value:
        provider_id = _provider_id(db, user_id, tenant_id)
        validate_transition(request.status, next_status, role, owns_provider=provider_id == request.provider_id)
    else:
        validate_transition(request.status, next_status, role, owns_branch=request.branch_id == branch_id)

    try:
        if next_status == ReplenishmentStatusEnum.delivered:
            receive_request(db, request, user_id)
        now = datetime.now(timezone.utc)
        request.status = next_status
        field = {ReplenishmentStatusEnum.accepted: "accepted", ReplenishmentStatusEnum.preparing: "preparing", ReplenishmentStatusEnum.awaiting_receipt: "awaiting_receipt", ReplenishmentStatusEnum.delivered: "delivered"}[next_status]
        setattr(request, f"{field}_by", user_id)
        setattr(request, f"{field}_at", now)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(request)
    return request


def receive_request(db: Session, request: ReplenishmentRequest, actor_id: UUID):
    _validate_references(db, request.provider_id, request.branch_id,
                         [item.variant_id for item in request.items], request.tenant_id)
    for item in request.items:
        inventory = _get_or_create_inventory(db, item.variant_id, request.branch_id, request.tenant_id)
        inventory.quantity += item.requested_quantity
        db.add(InventoryMovement(tenant_id=request.tenant_id, variant_id=item.variant_id, branch_id=request.branch_id, movement_type=InventoryMovementTypeEnum.income, quantity=item.requested_quantity, note=f"Solicitud de reposición {request.id}", created_by=actor_id))
