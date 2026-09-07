from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.reservation import Reservation
from app.models.reservation_item import ReservationItem
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.size import Size
from app.models.color import Color
from app.schemas.order_schema import PaymentMethodEnum, PaymentStatusEnum
from app.schemas.sales_schema import SaleCreate, SaleItemRead, SaleRead, SaleStatusEnum
from app.schemas.catalog_enums import ProductStatusEnum
from app.schemas.inventory_schema import InventoryMovementTypeEnum
from app.schemas.reservation_schema import ReservationStatusEnum


def _get_inventory_for_update(db: Session, variant_id, branch_id) -> Inventory | None:
    return (
        db.query(Inventory)
        .filter(Inventory.variant_id == variant_id, Inventory.branch_id == branch_id)
        .with_for_update()
        .first()
    )


def _get_sale_for_branch(db: Session, sale_id: UUID, branch_id: UUID) -> Sale | None:
    return db.query(Sale).filter(Sale.id == sale_id, Sale.branch_id == branch_id).first()


def _get_reservation_for_branch(db: Session, reservation_id: UUID, branch_id: UUID) -> Reservation | None:
    return (
        db.query(Reservation)
        .filter(Reservation.id == reservation_id, Reservation.branch_id == branch_id)
        .with_for_update()
        .first()
    )


def _sale_items_query(db: Session, sale_id: UUID):
    return (
        db.query(
            SaleItem.id.label("id"),
            SaleItem.sale_id.label("sale_id"),
            SaleItem.variant_id.label("variant_id"),
            SaleItem.quantity.label("quantity"),
            SaleItem.unit_price.label("unit_price"),
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
        .join(ProductVariant, ProductVariant.id == SaleItem.variant_id)
        .join(Product, Product.id == ProductVariant.product_id)
        .outerjoin(Size, Size.id == ProductVariant.size_id)
        .outerjoin(Color, Color.id == ProductVariant.color_id)
        .filter(SaleItem.sale_id == sale_id)
        .order_by(SaleItem.id.asc())
        .all()
    )


def _serialize_sale(db: Session, sale: Sale) -> SaleRead:
    item_rows = _sale_items_query(db, sale.id)
    items = []
    for row in item_rows:
        data = row._mapping
        line_total = Decimal(str(data["unit_price"])) * int(data["quantity"])
        items.append(
            SaleItemRead.model_validate(
                {
                    **data,
                    "line_total": line_total,
                }
            ).model_dump()
        )

    branch_name = db.query(Branch.name).filter(Branch.id == sale.branch_id).scalar() or str(sale.branch_id)

    return SaleRead.model_validate(
        {
            "id": sale.id,
            "branch_id": sale.branch_id,
            "branch_name": branch_name,
            "user_id": sale.user_id,
            "reservation_id": sale.reservation_id,
            "status": sale.status,
            "payment_method": sale.payment_method,
            "payment_status": sale.payment_status,
            "cash_reference": sale.cash_reference,
            "subtotal": sale.subtotal,
            "discount_amount": sale.discount_amount,
            "total_amount": sale.total_amount,
            "currency": sale.currency,
            "created_at": sale.created_at,
            "updated_at": sale.updated_at,
            "items": items,
        }
    )


def _resolve_items(db: Session, payload: SaleCreate, branch_id: UUID):
    normalized_items: dict[UUID, int] = defaultdict(int)

    if payload.reservation_id:
        reservation = _get_reservation_for_branch(db, payload.reservation_id, branch_id)
        if not reservation:
            raise ValueError("Reserva no encontrada para esta sucursal")
        if reservation.status in {ReservationStatusEnum.cancelled, ReservationStatusEnum.expired}:
            raise ValueError("La reserva no puede convertirse en venta")

        for item in reservation.items:
            normalized_items[item.variant_id] += item.quantity
    else:
        for item in payload.items:
            normalized_items[item.variant_id] += item.quantity

    if not normalized_items:
        raise ValueError("La venta no tiene items")

    return normalized_items


def _create_sale_from_items(
    db: Session,
    branch_id: UUID,
    user_id: UUID,
    payload: SaleCreate,
    normalized_items: dict[UUID, int],
):
    reservation = None
    reservation_should_adjust_inventory = False
    if payload.reservation_id:
        reservation = _get_reservation_for_branch(db, payload.reservation_id, branch_id)
        if not reservation:
            raise ValueError("Reserva no encontrada para esta sucursal")
        reservation_should_adjust_inventory = reservation.status in {ReservationStatusEnum.pending, ReservationStatusEnum.confirmed}

    sale = Sale(
        branch_id=branch_id,
        user_id=user_id,
        reservation_id=payload.reservation_id,
        status=SaleStatusEnum.completed,
        payment_method=payload.payment_method,
        payment_status=PaymentStatusEnum.paid,
        cash_reference=payload.cash_reference,
        subtotal=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("0.00"),
        currency="usd",
    )
    db.add(sale)
    db.flush()

    subtotal = Decimal("0.00")
    for variant_id, quantity in normalized_items.items():
        inventory = _get_inventory_for_update(db, variant_id, branch_id)
        if not inventory:
            raise ValueError("No existe inventario para la variante seleccionada")

        variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if not variant or variant.status != ProductStatusEnum.active:
            raise ValueError("Variante no disponible para la venta")

        if payload.reservation_id and reservation_should_adjust_inventory:
            reserved_quantity = int(inventory.reserved_quantity or 0)
            stock_quantity = int(inventory.quantity or 0)
            if stock_quantity < quantity:
                raise ValueError("No hay stock suficiente para completar la venta")
            if reserved_quantity < quantity:
                raise ValueError("La reserva ya no tiene stock suficiente")
            inventory.reserved_quantity = reserved_quantity - quantity
            inventory.quantity = stock_quantity - quantity
            movement_note = f"Venta presencial desde reserva {payload.reservation_id}"
        elif payload.reservation_id:
            movement_note = f"Venta presencial desde reserva {payload.reservation_id}"
        else:
            available = max((inventory.quantity or 0) - (inventory.reserved_quantity or 0), 0)
            if quantity > available:
                raise ValueError("No hay stock suficiente para completar la venta")
            inventory.quantity = (inventory.quantity or 0) - quantity
            movement_note = "Venta presencial"

        line_total = Decimal(str(variant.price)) * quantity
        subtotal += line_total
        db.add(
            SaleItem(
                sale_id=sale.id,
                variant_id=variant_id,
                quantity=quantity,
                unit_price=variant.price,
                line_total=line_total,
                product_id=variant.product_id,
                product_name=variant.product.name if variant.product else str(variant.product_id),
                variant_sku=variant.sku,
                size_id=variant.size_id,
                color_id=variant.color_id,
                image_url=variant.image_url,
                image_public_id=variant.image_public_id,
            )
        )
        if not payload.reservation_id or reservation_should_adjust_inventory:
            db.add(
                InventoryMovement(
                    variant_id=variant_id,
                    branch_id=branch_id,
                    movement_type=InventoryMovementTypeEnum.outcome,
                    quantity=quantity,
                    note=movement_note,
                    created_by=user_id,
                )
            )

    sale.subtotal = subtotal
    sale.discount_amount = Decimal("0.00")
    sale.total_amount = subtotal

    if reservation:
        if reservation.status in {ReservationStatusEnum.pending, ReservationStatusEnum.confirmed}:
            reservation.status = ReservationStatusEnum.attended
        elif reservation.status == ReservationStatusEnum.attended:
            reservation.status = ReservationStatusEnum.attended

    return sale


def create_sale(db: Session, user_id: UUID, payload: SaleCreate, branch_id: UUID):
    try:
        normalized_items = _resolve_items(db, payload, branch_id)
        with db.begin_nested():
            sale = _create_sale_from_items(db, branch_id, user_id, payload, normalized_items)
        db.commit()
        db.refresh(sale)
        return _serialize_sale(db, sale).model_dump()
    except Exception:
        db.rollback()
        raise


def list_sales_by_branch(db: Session, branch_id: UUID):
    sales = db.query(Sale).filter(Sale.branch_id == branch_id).order_by(Sale.created_at.desc()).all()
    return [_serialize_sale(db, sale).model_dump() for sale in sales]


def get_sale(db: Session, branch_id: UUID, sale_id: UUID):
    sale = _get_sale_for_branch(db, sale_id, branch_id)
    if not sale:
        return None
    return _serialize_sale(db, sale).model_dump()
