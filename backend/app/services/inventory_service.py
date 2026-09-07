from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.size import Size
from app.models.color import Color
from app.schemas.inventory_schema import (
    InventoryMovementCreate,
    InventoryMovementRead,
    InventoryMovementTypeEnum,
    InventoryTransferCreate,
)


def _inventory_available(inventory: Inventory) -> int:
    return max((inventory.quantity or 0) - (inventory.reserved_quantity or 0), 0)


def _get_inventory(db: Session, variant_id, branch_id) -> Inventory | None:
    return (
        db.query(Inventory)
        .filter(Inventory.variant_id == variant_id, Inventory.branch_id == branch_id)
        .first()
    )


def _get_or_create_inventory(db: Session, variant_id, branch_id) -> Inventory:
    inventory = _get_inventory(db, variant_id, branch_id)
    if inventory:
        return inventory

    inventory = Inventory(variant_id=variant_id, branch_id=branch_id, quantity=0, reserved_quantity=0)
    db.add(inventory)
    db.flush()
    return inventory


def _movement_to_read(movement: InventoryMovement) -> InventoryMovementRead:
    return InventoryMovementRead.model_validate(movement).model_dump()


def _serialize_stock_rows(rows):
    return [dict(row) for row in rows]


def get_branch_stock(db: Session, branch_id):
    rows = (
        db.query(
            Inventory.variant_id.label("variant_id"),
            Inventory.branch_id.label("branch_id"),
            Branch.name.label("branch_name"),
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            ProductVariant.sku.label("variant_sku"),
            ProductVariant.price.label("variant_price"),
            ProductVariant.image_url.label("image_url"),
            ProductVariant.image_public_id.label("image_public_id"),
            ProductVariant.status.label("status"),
            ProductVariant.size_id.label("size_id"),
            ProductVariant.color_id.label("color_id"),
            Size.name.label("size_name"),
            Color.name.label("color_name"),
            Inventory.quantity.label("quantity"),
            Inventory.reserved_quantity.label("reserved_quantity"),
        )
        .join(ProductVariant, ProductVariant.id == Inventory.variant_id)
        .join(Product, Product.id == ProductVariant.product_id)
        .join(Branch, Branch.id == Inventory.branch_id)
        .outerjoin(Size, Size.id == ProductVariant.size_id)
        .outerjoin(Color, Color.id == ProductVariant.color_id)
        .filter(Inventory.branch_id == branch_id)
        .order_by(Product.name.asc(), ProductVariant.sku.asc())
        .all()
    )

    result = []
    for row in rows:
        data = row._mapping
        quantity = int(data["quantity"] or 0)
        reserved = int(data["reserved_quantity"] or 0)
        result.append(
            {
                "variant_id": data["variant_id"],
                "branch_id": data["branch_id"],
                "branch_name": data["branch_name"],
                "product_id": data["product_id"],
                "product_name": data["product_name"],
                "variant_sku": data["variant_sku"],
                "variant_price": str(data["variant_price"]),
                "image_url": data["image_url"],
                "image_public_id": data["image_public_id"],
                "status": data["status"],
                "size_id": data["size_id"],
                "color_id": data["color_id"],
                "size_name": data["size_name"],
                "color_name": data["color_name"],
                "quantity": quantity,
                "reserved_quantity": reserved,
                "available_quantity": max(quantity - reserved, 0),
            }
        )
    return result


def get_consolidated_stock(db: Session):
    rows = (
        db.query(
            Inventory.variant_id.label("variant_id"),
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            ProductVariant.sku.label("variant_sku"),
            ProductVariant.price.label("variant_price"),
            ProductVariant.image_url.label("image_url"),
            ProductVariant.image_public_id.label("image_public_id"),
            ProductVariant.status.label("status"),
            ProductVariant.size_id.label("size_id"),
            ProductVariant.color_id.label("color_id"),
            Size.name.label("size_name"),
            Color.name.label("color_name"),
            Branch.id.label("branch_id"),
            Branch.name.label("branch_name"),
            Inventory.quantity.label("quantity"),
            Inventory.reserved_quantity.label("reserved_quantity"),
        )
        .join(ProductVariant, ProductVariant.id == Inventory.variant_id)
        .join(Product, Product.id == ProductVariant.product_id)
        .join(Branch, Branch.id == Inventory.branch_id)
        .outerjoin(Size, Size.id == ProductVariant.size_id)
        .outerjoin(Color, Color.id == ProductVariant.color_id)
        .order_by(Product.name.asc(), ProductVariant.sku.asc(), Branch.name.asc())
        .all()
    )

    grouped = {}
    for row in rows:
        data = row._mapping
        variant_id = data["variant_id"]
        quantity = int(data["quantity"] or 0)
        reserved = int(data["reserved_quantity"] or 0)
        entry = grouped.setdefault(
            variant_id,
            {
                "variant_id": variant_id,
                "product_id": data["product_id"],
                "product_name": data["product_name"],
                "variant_sku": data["variant_sku"],
                "variant_price": str(data["variant_price"]),
                "image_url": data["image_url"],
                "image_public_id": data["image_public_id"],
                "status": data["status"],
                "size_id": data["size_id"],
                "color_id": data["color_id"],
                "size_name": data["size_name"],
                "color_name": data["color_name"],
                "quantity": 0,
                "reserved_quantity": 0,
                "available_quantity": 0,
                "branches": [],
            },
        )
        entry["quantity"] += quantity
        entry["reserved_quantity"] += reserved
        entry["available_quantity"] += max(quantity - reserved, 0)
        entry["branches"].append(
            {
                "branch_id": data["branch_id"],
                "branch_name": data["branch_name"],
                "quantity": quantity,
                "reserved_quantity": reserved,
                "available_quantity": max(quantity - reserved, 0),
            }
        )

    return list(grouped.values())


def list_movements(db: Session, variant_id=None, branch_id=None, movement_type: InventoryMovementTypeEnum | None = None, limit: int = 100):
    query = db.query(InventoryMovement)
    if variant_id is not None:
        query = query.filter(InventoryMovement.variant_id == variant_id)
    if branch_id is not None:
        query = query.filter(InventoryMovement.branch_id == branch_id)
    if movement_type is not None:
        query = query.filter(InventoryMovement.movement_type == movement_type)

    return [
        _movement_to_read(movement)
        for movement in query.order_by(InventoryMovement.created_at.desc()).limit(limit).all()
    ]


def register_income(db: Session, payload: InventoryMovementCreate, created_by=None):
    inventory = _get_or_create_inventory(db, payload.variant_id, payload.branch_id)
    inventory.quantity += payload.quantity
    movement = InventoryMovement(
        variant_id=payload.variant_id,
        branch_id=payload.branch_id,
        movement_type=InventoryMovementTypeEnum.income,
        quantity=payload.quantity,
        note=payload.note,
        created_by=created_by,
    )
    db.add(movement)
    db.commit()
    db.refresh(inventory)
    db.refresh(movement)
    return movement, inventory


def register_outcome(db: Session, payload: InventoryMovementCreate, created_by=None):
    inventory = _get_or_create_inventory(db, payload.variant_id, payload.branch_id)
    if _inventory_available(inventory) < payload.quantity:
        raise ValueError("No hay stock disponible suficiente")

    inventory.quantity -= payload.quantity
    movement = InventoryMovement(
        variant_id=payload.variant_id,
        branch_id=payload.branch_id,
        movement_type=InventoryMovementTypeEnum.outcome,
        quantity=payload.quantity,
        note=payload.note,
        created_by=created_by,
    )
    db.add(movement)
    db.commit()
    db.refresh(inventory)
    db.refresh(movement)
    return movement, inventory


def register_transfer(db: Session, payload: InventoryTransferCreate, created_by=None):
    if payload.from_branch_id == payload.to_branch_id:
        raise ValueError("La sucursal origen y destino no pueden ser iguales")

    source_inventory = _get_or_create_inventory(db, payload.variant_id, payload.from_branch_id)
    if _inventory_available(source_inventory) < payload.quantity:
        raise ValueError("No hay stock disponible suficiente en la sucursal origen")

    destination_inventory = _get_or_create_inventory(db, payload.variant_id, payload.to_branch_id)
    source_inventory.quantity -= payload.quantity
    destination_inventory.quantity += payload.quantity

    out_movement = InventoryMovement(
        variant_id=payload.variant_id,
        branch_id=payload.from_branch_id,
        movement_type=InventoryMovementTypeEnum.transfer_out,
        quantity=payload.quantity,
        reference_branch_id=payload.to_branch_id,
        note=payload.note,
        created_by=created_by,
    )
    in_movement = InventoryMovement(
        variant_id=payload.variant_id,
        branch_id=payload.to_branch_id,
        movement_type=InventoryMovementTypeEnum.transfer_in,
        quantity=payload.quantity,
        reference_branch_id=payload.from_branch_id,
        note=payload.note,
        created_by=created_by,
    )
    db.add(out_movement)
    db.add(in_movement)
    db.commit()
    db.refresh(source_inventory)
    db.refresh(destination_inventory)
    db.refresh(out_movement)
    db.refresh(in_movement)
    return [out_movement, in_movement], [source_inventory, destination_inventory]
