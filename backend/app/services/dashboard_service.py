from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.reservation import Reservation
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.schemas.inventory_schema import InventoryMovementTypeEnum
from app.schemas.reservation_schema import ReservationStatusEnum
from app.schemas.dashboard_schema import (
    DashboardBranchKpi,
    DashboardInventoryPoint,
    DashboardMovementPoint,
    DashboardProductKpi,
    DashboardQuery,
    DashboardResponse,
    DashboardSeriesPoint,
    DashboardSummary,
)


def _date_range(filters: DashboardQuery):
    start = datetime.combine(filters.from_date, datetime.min.time()) if filters.from_date else None
    end = datetime.combine(filters.to_date + timedelta(days=1), datetime.min.time()) if filters.to_date else None
    return start, end


def _period_label(column, period: str):
    return func.to_char(func.date_trunc(period, column), 'YYYY-MM-DD')


def _collect_rows(rows, key_field: str) -> dict:
    return {str(getattr(row, key_field)): row._mapping for row in rows}


def get_dashboard(db: Session, filters: DashboardQuery) -> DashboardResponse:
    start, end = _date_range(filters)

    sales_total_row = (
        db.query(
            func.coalesce(func.sum(Sale.total_amount), 0).label('total_sales'),
            func.count(Sale.id).label('total_orders'),
        )
    )
    if filters.branch_id:
        sales_total_row = sales_total_row.filter(Sale.branch_id == filters.branch_id)
    if start:
        sales_total_row = sales_total_row.filter(Sale.created_at >= start)
    if end:
        sales_total_row = sales_total_row.filter(Sale.created_at < end)
    sales_total_row = sales_total_row.one()

    sales_units_row = (
        db.query(func.coalesce(func.sum(SaleItem.quantity), 0).label('total_units_sold'))
        .join(Sale, Sale.id == SaleItem.sale_id)
    )
    if filters.branch_id:
        sales_units_row = sales_units_row.filter(Sale.branch_id == filters.branch_id)
    if start:
        sales_units_row = sales_units_row.filter(Sale.created_at >= start)
    if end:
        sales_units_row = sales_units_row.filter(Sale.created_at < end)
    sales_units_row = sales_units_row.one()

    total_sales = Decimal(str(sales_total_row.total_sales or 0))
    total_orders = int(sales_total_row.total_orders or 0)
    total_units_sold = int(sales_units_row.total_units_sold or 0)

    inventory_aggregate = db.query(
        func.coalesce(func.sum(Inventory.quantity), 0).label('total_stock'),
        func.coalesce(func.sum(Inventory.quantity - Inventory.reserved_quantity), 0).label('total_available_stock'),
        func.coalesce(func.sum(case((Inventory.quantity <= Inventory.reserved_quantity, 1), else_=0)), 0).label('low_stock_items'),
    )
    if filters.branch_id:
        inventory_aggregate = inventory_aggregate.filter(Inventory.branch_id == filters.branch_id)
    inventory_row = inventory_aggregate.one()

    reservation_aggregate = db.query(
        func.count(Reservation.id).label('total_reservations'),
        func.coalesce(func.sum(case((Reservation.status == ReservationStatusEnum.pending, 1), else_=0)), 0).label('pending_reservations'),
        func.coalesce(func.sum(case((Reservation.status == ReservationStatusEnum.confirmed, 1), else_=0)), 0).label('confirmed_reservations'),
        func.coalesce(func.sum(case((Reservation.status == ReservationStatusEnum.attended, 1), else_=0)), 0).label('attended_reservations'),
        func.coalesce(func.sum(case((Reservation.status == ReservationStatusEnum.cancelled, 1), else_=0)), 0).label('cancelled_reservations'),
    )
    if filters.branch_id:
        reservation_aggregate = reservation_aggregate.filter(Reservation.branch_id == filters.branch_id)
    if start:
        reservation_aggregate = reservation_aggregate.filter(Reservation.created_at >= start)
    if end:
        reservation_aggregate = reservation_aggregate.filter(Reservation.created_at < end)
    reservation_row = reservation_aggregate.one()

    sales_period = _period_label(Sale.created_at, filters.period)
    sales_series_query = db.query(
        sales_period.label('label'),
        func.coalesce(func.sum(Sale.total_amount), 0).label('sales'),
        func.count(Sale.id).label('orders'),
    )
    if filters.branch_id:
        sales_series_query = sales_series_query.filter(Sale.branch_id == filters.branch_id)
    if start:
        sales_series_query = sales_series_query.filter(Sale.created_at >= start)
    if end:
        sales_series_query = sales_series_query.filter(Sale.created_at < end)
    sales_series_rows = sales_series_query.group_by(sales_period).order_by(sales_period).all()

    sales_units_series_query = db.query(
        sales_period.label('label'),
        func.coalesce(func.sum(SaleItem.quantity), 0).label('units'),
    ).join(Sale, Sale.id == SaleItem.sale_id)
    if filters.branch_id:
        sales_units_series_query = sales_units_series_query.filter(Sale.branch_id == filters.branch_id)
    if start:
        sales_units_series_query = sales_units_series_query.filter(Sale.created_at >= start)
    if end:
        sales_units_series_query = sales_units_series_query.filter(Sale.created_at < end)
    sales_units_series_rows = sales_units_series_query.group_by(sales_period).order_by(sales_period).all()
    sales_units_map = _collect_rows(sales_units_series_rows, 'label')

    movement_period = _period_label(InventoryMovement.created_at, filters.period)
    movement_series_query = db.query(
        movement_period.label('label'),
        func.coalesce(func.sum(case((InventoryMovement.movement_type == InventoryMovementTypeEnum.income, InventoryMovement.quantity), else_=0)), 0).label('income'),
        func.coalesce(func.sum(case((InventoryMovement.movement_type == InventoryMovementTypeEnum.outcome, InventoryMovement.quantity), else_=0)), 0).label('outcome'),
        func.coalesce(func.sum(case((InventoryMovement.movement_type == InventoryMovementTypeEnum.transfer_in, InventoryMovement.quantity), else_=0)), 0).label('transfer_in'),
        func.coalesce(func.sum(case((InventoryMovement.movement_type == InventoryMovementTypeEnum.transfer_out, InventoryMovement.quantity), else_=0)), 0).label('transfer_out'),
    )
    if filters.branch_id:
        movement_series_query = movement_series_query.filter(InventoryMovement.branch_id == filters.branch_id)
    if start:
        movement_series_query = movement_series_query.filter(InventoryMovement.created_at >= start)
    if end:
        movement_series_query = movement_series_query.filter(InventoryMovement.created_at < end)
    movement_series_rows = movement_series_query.group_by(movement_period).order_by(movement_period).all()

    branch_sales_amount_rows = db.query(
        Sale.branch_id.label('branch_id'),
        func.coalesce(func.sum(Sale.total_amount), 0).label('total_sales'),
        func.count(Sale.id).label('total_orders'),
    )
    if filters.branch_id:
        branch_sales_amount_rows = branch_sales_amount_rows.filter(Sale.branch_id == filters.branch_id)
    if start:
        branch_sales_amount_rows = branch_sales_amount_rows.filter(Sale.created_at >= start)
    if end:
        branch_sales_amount_rows = branch_sales_amount_rows.filter(Sale.created_at < end)
    branch_sales_amount_rows = branch_sales_amount_rows.group_by(Sale.branch_id).all()

    branch_sales_units_rows = db.query(
        Sale.branch_id.label('branch_id'),
        func.coalesce(func.sum(SaleItem.quantity), 0).label('total_units_sold'),
    ).join(Sale, Sale.id == SaleItem.sale_id)
    if filters.branch_id:
        branch_sales_units_rows = branch_sales_units_rows.filter(Sale.branch_id == filters.branch_id)
    if start:
        branch_sales_units_rows = branch_sales_units_rows.filter(Sale.created_at >= start)
    if end:
        branch_sales_units_rows = branch_sales_units_rows.filter(Sale.created_at < end)
    branch_sales_units_rows = branch_sales_units_rows.group_by(Sale.branch_id).all()

    branch_sales_map = {str(row.branch_id): row._mapping for row in branch_sales_amount_rows}
    branch_sales_units_map = {str(row.branch_id): row._mapping for row in branch_sales_units_rows}

    branch_inventory_rows = (
        db.query(
            Inventory.branch_id.label('branch_id'),
            func.coalesce(func.sum(Inventory.quantity), 0).label('total_stock'),
            func.coalesce(func.sum(Inventory.quantity - Inventory.reserved_quantity), 0).label('total_available_stock'),
        )
        .group_by(Inventory.branch_id)
        .all()
    )
    if filters.branch_id:
        branch_inventory_rows = [row for row in branch_inventory_rows if str(row.branch_id) == str(filters.branch_id)]
    branch_inventory_map = {str(row.branch_id): row._mapping for row in branch_inventory_rows}

    branch_rows = []
    branch_query = db.query(Branch.id, Branch.name, Branch.city)
    if filters.branch_id:
        branch_query = branch_query.filter(Branch.id == filters.branch_id)
    for branch in branch_query.order_by(Branch.name.asc()).all():
        sales_data = branch_sales_map.get(str(branch.id), {})
        units_data = branch_sales_units_map.get(str(branch.id), {})
        inventory_data = branch_inventory_map.get(str(branch.id), {})
        branch_rows.append(
            DashboardBranchKpi(
                branch_id=branch.id,
                branch_name=branch.name,
                city=branch.city,
                total_sales=Decimal(str(sales_data.get('total_sales', 0) or 0)),
                total_orders=int(sales_data.get('total_orders', 0) or 0),
                total_units_sold=int(units_data.get('total_units_sold', 0) or 0),
                total_stock=int(inventory_data.get('total_stock', 0) or 0),
                total_available_stock=int(inventory_data.get('total_available_stock', 0) or 0),
            )
        )

    product_sales_query = db.query(
        Product.id.label('product_id'),
        Product.name.label('product_name'),
        func.coalesce(func.sum(SaleItem.quantity), 0).label('total_units_sold'),
        func.coalesce(func.sum(SaleItem.line_total), 0).label('total_sales'),
    ).join(Sale, Sale.id == SaleItem.sale_id).join(ProductVariant, ProductVariant.id == SaleItem.variant_id).join(Product, Product.id == ProductVariant.product_id)
    if filters.branch_id:
        product_sales_query = product_sales_query.filter(Sale.branch_id == filters.branch_id)
    if start:
        product_sales_query = product_sales_query.filter(Sale.created_at >= start)
    if end:
        product_sales_query = product_sales_query.filter(Sale.created_at < end)
    product_sales_rows = product_sales_query.group_by(Product.id, Product.name).all()
    product_sales_map = {str(row.product_id): row._mapping for row in product_sales_rows}

    product_inventory_rows = (
        db.query(
            Product.id.label('product_id'),
            func.coalesce(func.sum(Inventory.quantity), 0).label('total_stock'),
            func.coalesce(func.sum(Inventory.quantity - Inventory.reserved_quantity), 0).label('total_available_stock'),
        )
        .join(ProductVariant, ProductVariant.product_id == Product.id)
        .join(Inventory, Inventory.variant_id == ProductVariant.id)
    )
    if filters.branch_id:
        product_inventory_rows = product_inventory_rows.filter(Inventory.branch_id == filters.branch_id)
    product_inventory_rows = product_inventory_rows.group_by(Product.id).all()
    product_inventory_map = {str(row.product_id): row._mapping for row in product_inventory_rows}

    product_rows = []
    product_query = db.query(Product.id, Product.name)
    for product in product_query.order_by(Product.name.asc()).all():
        sales_data = product_sales_map.get(str(product.id), {})
        inventory_data = product_inventory_map.get(str(product.id), {})
        product_rows.append(
            DashboardProductKpi(
                product_id=product.id,
                product_name=product.name,
                total_units_sold=int(sales_data.get('total_units_sold', 0) or 0),
                total_sales=Decimal(str(sales_data.get('total_sales', 0) or 0)),
                total_stock=int(inventory_data.get('total_stock', 0) or 0),
                total_available_stock=int(inventory_data.get('total_available_stock', 0) or 0),
            )
        )
    product_rows.sort(key=lambda item: (item.total_sales, item.total_units_sold), reverse=True)
    product_rows = product_rows[:10]

    low_stock_rows = (
        db.query(
            Branch.name.label('branch_name'),
            Product.name.label('product_name'),
            ProductVariant.sku.label('variant_sku'),
            Inventory.quantity.label('quantity'),
            Inventory.reserved_quantity.label('reserved_quantity'),
            (Inventory.quantity - Inventory.reserved_quantity).label('available_quantity'),
        )
        .join(ProductVariant, ProductVariant.id == Inventory.variant_id)
        .join(Product, Product.id == ProductVariant.product_id)
        .outerjoin(Branch, Branch.id == Inventory.branch_id)
        .filter(Inventory.quantity <= Inventory.reserved_quantity)
    )
    if filters.branch_id:
        low_stock_rows = low_stock_rows.filter(Inventory.branch_id == filters.branch_id)
    low_stock_rows = low_stock_rows.order_by(Branch.name.asc().nullslast(), Product.name.asc(), ProductVariant.sku.asc()).limit(8).all()

    summary = DashboardSummary(
        total_sales=total_sales,
        total_orders=total_orders,
        total_units_sold=total_units_sold,
        average_ticket=(total_sales / total_orders) if total_orders else Decimal('0.00'),
        total_stock=int(inventory_row.total_stock or 0),
        total_available_stock=int(inventory_row.total_available_stock or 0),
        low_stock_items=int(inventory_row.low_stock_items or 0),
        total_reservations=int(reservation_row.total_reservations or 0),
        pending_reservations=int(reservation_row.pending_reservations or 0),
        confirmed_reservations=int(reservation_row.confirmed_reservations or 0),
        attended_reservations=int(reservation_row.attended_reservations or 0),
        cancelled_reservations=int(reservation_row.cancelled_reservations or 0),
    )

    return DashboardResponse(
        filters=filters,
        summary=summary,
        sales_series=[
            DashboardSeriesPoint(
                label=row.label,
                sales=Decimal(str(row.sales or 0)),
                orders=int(row.orders or 0),
                units=int(sales_units_map.get(str(row.label), {}).get('units', 0) or 0),
            )
            for row in sales_series_rows
        ],
        movement_series=[
            DashboardMovementPoint(
                label=row.label,
                income=int(row.income or 0),
                outcome=int(row.outcome or 0),
                transfer_in=int(row.transfer_in or 0),
                transfer_out=int(row.transfer_out or 0),
            )
            for row in movement_series_rows
        ],
        branch_kpis=branch_rows,
        top_products=product_rows,
        low_stock=[DashboardInventoryPoint.model_validate(row._mapping) for row in low_stock_rows],
    )
