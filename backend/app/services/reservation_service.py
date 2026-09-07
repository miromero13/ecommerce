from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.branch import Branch
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.reservation import Reservation
from app.models.reservation_item import ReservationItem
from app.models.size import Size
from app.models.color import Color
from app.schemas.catalog_enums import ProductStatusEnum
from app.schemas.reservation_schema import ReservationCreate, ReservationItemRead, ReservationRead, ReservationStatusEnum


ACTIVE_RESERVATION_STATUSES = {ReservationStatusEnum.pending, ReservationStatusEnum.confirmed}


def _get_inventory_for_update(db: Session, variant_id, branch_id) -> Inventory | None:
    return (
        db.query(Inventory)
        .filter(Inventory.variant_id == variant_id, Inventory.branch_id == branch_id)
        .with_for_update()
        .first()
    )


def _available_quantity(inventory: Inventory | None) -> int:
    if not inventory:
        return 0
    return max((inventory.quantity or 0) - (inventory.reserved_quantity or 0), 0)


def _reservation_items_query(db: Session, reservation_id: UUID):
    return (
        db.query(
            ReservationItem.id.label("id"),
            ReservationItem.reservation_id.label("reservation_id"),
            ReservationItem.variant_id.label("variant_id"),
            ReservationItem.quantity.label("quantity"),
            ReservationItem.unit_price.label("unit_price"),
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            ProductVariant.sku.label("variant_sku"),
            ProductVariant.size_id.label("size_id"),
            ProductVariant.color_id.label("color_id"),
            ProductVariant.image_url.label("image_url"),
            ProductVariant.image_public_id.label("image_public_id"),
            Size.name.label("size_name"),
            Color.name.label("color_name"),
        )
        .join(ProductVariant, ProductVariant.id == ReservationItem.variant_id)
        .join(Product, Product.id == ProductVariant.product_id)
        .outerjoin(Size, Size.id == ProductVariant.size_id)
        .outerjoin(Color, Color.id == ProductVariant.color_id)
        .filter(ReservationItem.reservation_id == reservation_id)
        .order_by(ReservationItem.id.asc())
        .all()
    )


def _serialize_reservation(db: Session, reservation: Reservation) -> ReservationRead:
    item_rows = _reservation_items_query(db, reservation.id)
    items = []
    total_amount = Decimal("0.00")
    item_count = 0

    for row in item_rows:
        data = row._mapping
        line_total = Decimal(str(data["unit_price"])) * int(data["quantity"])
        total_amount += line_total
        item_count += int(data["quantity"])
        items.append(
            ReservationItemRead.model_validate(
                {
                    **data,
                    "line_total": line_total,
                }
            ).model_dump()
        )

    branch_name = db.query(Branch.name).filter(Branch.id == reservation.branch_id).scalar() or str(reservation.branch_id)

    return ReservationRead.model_validate(
        {
            "id": reservation.id,
            "branch_id": reservation.branch_id,
            "branch_name": branch_name,
            "user_id": reservation.user_id,
            "visit_date": reservation.visit_date,
            "expires_at": reservation.expires_at,
            "status": reservation.status,
            "total_amount": total_amount,
            "item_count": item_count,
            "created_at": reservation.created_at,
            "updated_at": reservation.updated_at,
            "items": items,
        }
    )


def _get_reservation_for_user(db: Session, reservation_id: UUID, user_id: UUID) -> Reservation | None:
    return (
        db.query(Reservation)
        .options(joinedload(Reservation.items))
        .filter(Reservation.id == reservation_id, Reservation.user_id == user_id)
        .first()
    )


def expire_due_reservations(db: Session):
    today = date.today()
    reservations = (
        db.query(Reservation)
        .options(joinedload(Reservation.items))
        .filter(Reservation.status.in_(ACTIVE_RESERVATION_STATUSES), Reservation.expires_at <= today)
        .all()
    )

    if not reservations:
        return []

    expired = []
    for reservation in reservations:
        for item in reservation.items:
            inventory = _get_inventory_for_update(db, item.variant_id, reservation.branch_id)
            if inventory:
                inventory.reserved_quantity = max((inventory.reserved_quantity or 0) - item.quantity, 0)
        reservation.status = ReservationStatusEnum.expired
        expired.append(reservation)

    db.commit()
    return expired


def list_reservations(db: Session, user_id: UUID):
    expire_due_reservations(db)
    reservations = (
        db.query(Reservation)
        .filter(Reservation.user_id == user_id)
        .order_by(Reservation.created_at.desc())
        .all()
    )
    return [_serialize_reservation(db, reservation).model_dump() for reservation in reservations]


def list_reservations_by_branch(db: Session, branch_id: UUID):
    expire_due_reservations(db)
    reservations = (
        db.query(Reservation)
        .filter(Reservation.branch_id == branch_id)
        .order_by(Reservation.created_at.desc())
        .all()
    )
    return [_serialize_reservation(db, reservation).model_dump() for reservation in reservations]


def get_reservation(db: Session, user_id: UUID, reservation_id: UUID):
    expire_due_reservations(db)
    reservation = _get_reservation_for_user(db, reservation_id, user_id)
    if not reservation:
        return None
    return _serialize_reservation(db, reservation).model_dump()


def create_reservation(db: Session, user_id: UUID, payload: ReservationCreate):
    expire_due_reservations(db)

    normalized_items: dict[UUID, int] = defaultdict(int)
    for item in payload.items:
        normalized_items[item.variant_id] += item.quantity

    branch = db.query(Branch).filter(Branch.id == payload.branch_id).first()
    if not branch:
        raise ValueError("Sucursal no encontrada")
    if hasattr(branch, "is_active") and not branch.is_active:
        raise ValueError("Sucursal inactiva")

    with db.begin_nested():
        reservation = Reservation(
            branch_id=payload.branch_id,
            user_id=user_id,
            visit_date=payload.visit_date,
            expires_at=payload.visit_date + timedelta(days=1),
            status=ReservationStatusEnum.pending,
            total_amount=Decimal("0.00"),
        )
        db.add(reservation)
        db.flush()

        total_amount = Decimal("0.00")
        for variant_id, quantity in normalized_items.items():
            inventory = _get_inventory_for_update(db, variant_id, payload.branch_id)
            if not inventory:
                raise ValueError("No hay stock disponible suficiente para la reserva")

            available = _available_quantity(inventory)
            if quantity > available:
                raise ValueError("No hay stock disponible suficiente para la reserva")

            variant = (
                db.query(ProductVariant)
                .filter(ProductVariant.id == variant_id)
                .first()
            )
            if not variant or variant.status != ProductStatusEnum.active:
                raise ValueError("Variante no disponible para reserva")

            inventory.reserved_quantity = (inventory.reserved_quantity or 0) + quantity
            db.add(
                ReservationItem(
                    reservation_id=reservation.id,
                    variant_id=variant_id,
                    quantity=quantity,
                    unit_price=variant.price,
                )
            )
            total_amount += Decimal(str(variant.price)) * quantity

        reservation.total_amount = total_amount

    db.commit()

    db.refresh(reservation)
    return _serialize_reservation(db, reservation).model_dump()


def cancel_reservation(db: Session, user_id: UUID, reservation_id: UUID):
    expire_due_reservations(db)
    reservation = _get_reservation_for_user(db, reservation_id, user_id)
    if not reservation:
        return None
    if reservation.status in {ReservationStatusEnum.cancelled, ReservationStatusEnum.expired, ReservationStatusEnum.attended}:
        raise ValueError("La reserva no se puede cancelar")

    with db.begin_nested():
        for item in reservation.items:
            inventory = _get_inventory_for_update(db, item.variant_id, reservation.branch_id)
            if inventory:
                inventory.reserved_quantity = max((inventory.reserved_quantity or 0) - item.quantity, 0)
        reservation.status = ReservationStatusEnum.cancelled

    db.commit()

    db.refresh(reservation)
    return _serialize_reservation(db, reservation).model_dump()


def _get_branch_reservation(db: Session, reservation_id: UUID, branch_id: UUID) -> Reservation | None:
    return (
        db.query(Reservation)
        .options(joinedload(Reservation.items))
        .filter(Reservation.id == reservation_id, Reservation.branch_id == branch_id)
        .first()
    )


def confirm_reservation_arrival(db: Session, reservation_id: UUID, branch_id: UUID):
    expire_due_reservations(db)
    reservation = _get_branch_reservation(db, reservation_id, branch_id)
    if not reservation:
        return None
    if reservation.status in {ReservationStatusEnum.cancelled, ReservationStatusEnum.expired, ReservationStatusEnum.attended}:
        raise ValueError("La reserva no puede confirmarse")

    reservation.status = ReservationStatusEnum.confirmed
    db.commit()
    db.refresh(reservation)
    return _serialize_reservation(db, reservation).model_dump()


def attend_reservation(db: Session, reservation_id: UUID, branch_id: UUID):
    expire_due_reservations(db)
    reservation = _get_branch_reservation(db, reservation_id, branch_id)
    if not reservation:
        return None
    if reservation.status in {ReservationStatusEnum.cancelled, ReservationStatusEnum.expired, ReservationStatusEnum.attended}:
        raise ValueError("La reserva no puede atenderse")

    try:
        for item in reservation.items:
            inventory = _get_inventory_for_update(db, item.variant_id, reservation.branch_id)
            if not inventory:
                raise ValueError("No existe inventario para la variante reservada")
            inventory.reserved_quantity = max((inventory.reserved_quantity or 0) - item.quantity, 0)
            inventory.quantity = max((inventory.quantity or 0) - item.quantity, 0)
        reservation.status = ReservationStatusEnum.attended
        db.commit()
        db.refresh(reservation)
        return _serialize_reservation(db, reservation).model_dump()
    except Exception:
        db.rollback()
        raise


def cancel_branch_reservation(db: Session, reservation_id: UUID, branch_id: UUID):
    expire_due_reservations(db)
    reservation = _get_branch_reservation(db, reservation_id, branch_id)
    if not reservation:
        return None
    if reservation.status in {ReservationStatusEnum.cancelled, ReservationStatusEnum.expired, ReservationStatusEnum.attended}:
        raise ValueError("La reserva no se puede cancelar")

    try:
        for item in reservation.items:
            inventory = _get_inventory_for_update(db, item.variant_id, reservation.branch_id)
            if inventory:
                inventory.reserved_quantity = max((inventory.reserved_quantity or 0) - item.quantity, 0)
        reservation.status = ReservationStatusEnum.cancelled
        db.commit()
        db.refresh(reservation)
        return _serialize_reservation(db, reservation).model_dump()
    except Exception:
        db.rollback()
        raise


def list_reservation_statuses():
    return [status.value for status in ReservationStatusEnum]
