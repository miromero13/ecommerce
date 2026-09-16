from __future__ import annotations

import csv
from enum import Enum
from datetime import date, datetime, timedelta
from decimal import Decimal
from io import StringIO
from typing import Iterable

from sqlalchemy import func, literal, or_
from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.schemas.report_schema import InventoryReportRow, MovementReportRow, ReportQuery, ReportSummary, SalesReportRow
from app.schemas.sales_schema import SaleTypeEnum


def _date_range(filters: ReportQuery):
    start = datetime.combine(filters.from_date, datetime.min.time()) if filters.from_date else None
    end = datetime.combine(filters.to_date + timedelta(days=1), datetime.min.time()) if filters.to_date else None
    return start, end


def get_sales_report(db: Session, filters: ReportQuery):
    start, end = _date_range(filters)
    query = (
        db.query(
            Sale.branch_id.label("branch_id"),
            Branch.name.label("branch_name"),
            SaleItem.product_id.label("product_id"),
            SaleItem.product_name.label("product_name"),
            SaleItem.variant_id.label("variant_id"),
            SaleItem.variant_sku.label("variant_sku"),
            func.sum(SaleItem.quantity).label("quantity_sold"),
            func.sum(SaleItem.line_total).label("gross_sales"),
            Sale.payment_method.label("payment_method"),
            Sale.payment_status.label("payment_status"),
            Sale.status.label("sale_status"),
            literal(SaleTypeEnum.in_person.value).label("type"),
        )
        .join(SaleItem, SaleItem.sale_id == Sale.id)
        .outerjoin(Branch, Branch.id == Sale.branch_id)
    )

    if filters.branch_id:
        query = query.filter(Sale.branch_id == filters.branch_id)
    if filters.product_id:
        query = query.filter(SaleItem.product_id == filters.product_id)
    if filters.variant_id:
        query = query.filter(SaleItem.variant_id == filters.variant_id)
    if start:
        query = query.filter(Sale.created_at >= start)
    if end:
        query = query.filter(Sale.created_at < end)
    if filters.q:
        term = f"%{filters.q.strip()}%"
        query = query.filter(or_(SaleItem.product_name.ilike(term), SaleItem.variant_sku.ilike(term), Branch.name.ilike(term)))

    rows = query.group_by(
        Sale.branch_id,
        Branch.name,
        SaleItem.product_id,
        SaleItem.product_name,
        SaleItem.variant_id,
        SaleItem.variant_sku,
        Sale.payment_method,
        Sale.payment_status,
        Sale.status,
    ).order_by(Branch.name.asc().nullslast(), SaleItem.product_name.asc(), SaleItem.variant_sku.asc()).all()

    serialized = [SalesReportRow.model_validate(row._mapping).model_dump() for row in rows]
    online_query = (
        db.query(
            Order.pickup_branch_id.label("branch_id"), Branch.name.label("branch_name"),
            OrderItem.product_id.label("product_id"), OrderItem.product_name.label("product_name"),
            OrderItem.variant_id.label("variant_id"), OrderItem.variant_sku.label("variant_sku"),
            func.sum(OrderItem.quantity).label("quantity_sold"), func.sum(OrderItem.line_total).label("gross_sales"),
            Order.payment_method.label("payment_method"), Order.payment_status.label("payment_status"),
            literal("completed").label("sale_status"), literal(SaleTypeEnum.online.value).label("type"),
        ).join(OrderItem, OrderItem.order_id == Order.id)
        .outerjoin(Branch, Branch.id == Order.pickup_branch_id)
        .filter(Order.status == "paid", Order.pickup_branch_id.is_not(None))
    )
    if filters.branch_id:
        online_query = online_query.filter(Order.pickup_branch_id == filters.branch_id)
    if filters.product_id:
        online_query = online_query.filter(OrderItem.product_id == filters.product_id)
    if filters.variant_id:
        online_query = online_query.filter(OrderItem.variant_id == filters.variant_id)
    if start:
        online_query = online_query.filter(Order.created_at >= start)
    if end:
        online_query = online_query.filter(Order.created_at < end)
    if filters.q:
        term = f"%{filters.q.strip()}%"
        online_query = online_query.filter(or_(OrderItem.product_name.ilike(term), OrderItem.variant_sku.ilike(term), Branch.name.ilike(term)))
    online_rows = online_query.group_by(
        Order.pickup_branch_id, Branch.name, OrderItem.product_id, OrderItem.product_name,
        OrderItem.variant_id, OrderItem.variant_sku, Order.payment_method, Order.payment_status,
    ).order_by(Branch.name.asc().nullslast(), OrderItem.product_name.asc(), OrderItem.variant_sku.asc()).all()
    serialized.extend(SalesReportRow.model_validate(row._mapping).model_dump() for row in online_rows)
    total_orders = (
        db.query(func.count(func.distinct(Sale.id)))
        .join(SaleItem, SaleItem.sale_id == Sale.id)
        .outerjoin(Branch, Branch.id == Sale.branch_id)
    )
    if filters.branch_id:
        total_orders = total_orders.filter(Sale.branch_id == filters.branch_id)
    if filters.product_id:
        total_orders = total_orders.filter(SaleItem.product_id == filters.product_id)
    if filters.variant_id:
        total_orders = total_orders.filter(SaleItem.variant_id == filters.variant_id)
    if start:
        total_orders = total_orders.filter(Sale.created_at >= start)
    if end:
        total_orders = total_orders.filter(Sale.created_at < end)
    if filters.q:
        term = f"%{filters.q.strip()}%"
        total_orders = total_orders.filter(or_(SaleItem.product_name.ilike(term), SaleItem.variant_sku.ilike(term), Branch.name.ilike(term)))
    total_orders_value = int(total_orders.scalar() or 0)
    online_orders = db.query(func.count(func.distinct(Order.id))).join(OrderItem, OrderItem.order_id == Order.id).outerjoin(Branch, Branch.id == Order.pickup_branch_id).filter(Order.status == "paid", Order.pickup_branch_id.is_not(None))
    if filters.branch_id:
        online_orders = online_orders.filter(Order.pickup_branch_id == filters.branch_id)
    if filters.product_id:
        online_orders = online_orders.filter(OrderItem.product_id == filters.product_id)
    if filters.variant_id:
        online_orders = online_orders.filter(OrderItem.variant_id == filters.variant_id)
    if start:
        online_orders = online_orders.filter(Order.created_at >= start)
    if end:
        online_orders = online_orders.filter(Order.created_at < end)
    if filters.q:
        term = f"%{filters.q.strip()}%"
        online_orders = online_orders.filter(or_(OrderItem.product_name.ilike(term), OrderItem.variant_sku.ilike(term), Branch.name.ilike(term)))
    total_orders_value += int(online_orders.scalar() or 0)

    total_sales = sum(Decimal(str(row["gross_sales"])) for row in serialized)
    total_units = sum(int(row["quantity_sold"]) for row in serialized)

    return {
        "summary": ReportSummary(
            total_orders=total_orders_value,
            total_sales=total_sales,
            total_units=total_units,
            average_ticket=(total_sales / total_orders_value) if total_orders_value else Decimal("0.00"),
        ).model_dump(),
        "rows": serialized,
    }


def get_inventory_report(db: Session, filters: ReportQuery):
    query = (
        db.query(
            Inventory.branch_id.label("branch_id"),
            Branch.name.label("branch_name"),
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            Inventory.variant_id.label("variant_id"),
            ProductVariant.sku.label("variant_sku"),
            func.sum(Inventory.quantity).label("quantity"),
            func.sum(Inventory.reserved_quantity).label("reserved_quantity"),
            func.sum(Inventory.quantity - Inventory.reserved_quantity).label("available_quantity"),
        )
        .join(ProductVariant, ProductVariant.id == Inventory.variant_id)
        .join(Product, Product.id == ProductVariant.product_id)
        .outerjoin(Branch, Branch.id == Inventory.branch_id)
    )

    if filters.branch_id:
        query = query.filter(Inventory.branch_id == filters.branch_id)
    if filters.product_id:
        query = query.filter(Product.id == filters.product_id)
    if filters.variant_id:
        query = query.filter(Inventory.variant_id == filters.variant_id)
    if filters.q:
        term = f"%{filters.q.strip()}%"
        query = query.filter(or_(Product.name.ilike(term), ProductVariant.sku.ilike(term), Branch.name.ilike(term)))

    rows = query.group_by(
        Inventory.branch_id,
        Branch.name,
        Product.id,
        Product.name,
        Inventory.variant_id,
        ProductVariant.sku,
    ).order_by(Branch.name.asc().nullslast(), Product.name.asc(), ProductVariant.sku.asc()).all()

    serialized = [InventoryReportRow.model_validate(row._mapping).model_dump() for row in rows]
    return {
        "summary": {
            "total_lines": len(serialized),
            "total_stock": sum(int(row["quantity"]) for row in serialized),
            "total_reserved": sum(int(row["reserved_quantity"]) for row in serialized),
            "total_available": sum(int(row["available_quantity"]) for row in serialized),
        },
        "rows": serialized,
    }


def get_movements_report(db: Session, filters: ReportQuery):
    start, end = _date_range(filters)
    query = (
        db.query(
            InventoryMovement.branch_id.label("branch_id"),
            Branch.name.label("branch_name"),
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            InventoryMovement.variant_id.label("variant_id"),
            ProductVariant.sku.label("variant_sku"),
            InventoryMovement.movement_type.label("movement_type"),
            func.sum(InventoryMovement.quantity).label("quantity"),
            func.count(InventoryMovement.id).label("movements_count"),
        )
        .join(ProductVariant, ProductVariant.id == InventoryMovement.variant_id)
        .join(Product, Product.id == ProductVariant.product_id)
        .outerjoin(Branch, Branch.id == InventoryMovement.branch_id)
    )

    if filters.branch_id:
        query = query.filter(InventoryMovement.branch_id == filters.branch_id)
    if filters.product_id:
        query = query.filter(Product.id == filters.product_id)
    if filters.variant_id:
        query = query.filter(InventoryMovement.variant_id == filters.variant_id)
    if start:
        query = query.filter(InventoryMovement.created_at >= start)
    if end:
        query = query.filter(InventoryMovement.created_at < end)
    if filters.q:
        term = f"%{filters.q.strip()}%"
        query = query.filter(or_(Product.name.ilike(term), ProductVariant.sku.ilike(term), Branch.name.ilike(term)))

    rows = query.group_by(
        InventoryMovement.branch_id,
        Branch.name,
        Product.id,
        Product.name,
        InventoryMovement.variant_id,
        ProductVariant.sku,
        InventoryMovement.movement_type,
    ).order_by(Branch.name.asc().nullslast(), Product.name.asc(), ProductVariant.sku.asc()).all()

    serialized = [MovementReportRow.model_validate(row._mapping).model_dump() for row in rows]
    return {
        "summary": {
            "total_lines": len(serialized),
            "total_units_moved": sum(int(row["quantity"]) for row in serialized),
        },
        "rows": serialized,
    }


def export_rows_to_csv(rows: Iterable[dict], headers: list[str]) -> str:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers)
    writer.writeheader()
    for row in rows:
        normalized = {}
        for key in headers:
            value = row.get(key, "")
            if isinstance(value, Enum):
                value = value.value
            normalized[key] = value
        writer.writerow(normalized)
    return buffer.getvalue()
