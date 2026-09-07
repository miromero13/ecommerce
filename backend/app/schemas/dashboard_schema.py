from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


DashboardPeriod = Literal['day', 'week', 'month']


class DashboardQuery(BaseModel):
    branch_id: UUID | None = None
    from_date: date | None = None
    to_date: date | None = None
    period: DashboardPeriod = 'day'


class DashboardSummary(BaseModel):
    total_sales: Decimal = Decimal('0.00')
    total_orders: int = 0
    total_units_sold: int = 0
    average_ticket: Decimal = Decimal('0.00')
    total_stock: int = 0
    total_available_stock: int = 0
    low_stock_items: int = 0
    total_reservations: int = 0
    pending_reservations: int = 0
    confirmed_reservations: int = 0
    attended_reservations: int = 0
    cancelled_reservations: int = 0


class DashboardBranchKpi(BaseModel):
    branch_id: UUID
    branch_name: str
    city: str
    total_sales: Decimal = Decimal('0.00')
    total_orders: int = 0
    total_units_sold: int = 0
    total_stock: int = 0
    total_available_stock: int = 0


class DashboardProductKpi(BaseModel):
    product_id: UUID
    product_name: str
    total_units_sold: int = 0
    total_sales: Decimal = Decimal('0.00')
    total_stock: int = 0
    total_available_stock: int = 0


class DashboardSeriesPoint(BaseModel):
    label: str
    sales: Decimal = Decimal('0.00')
    orders: int = 0
    units: int = 0


class DashboardMovementPoint(BaseModel):
    label: str
    income: int = 0
    outcome: int = 0
    transfer_in: int = 0
    transfer_out: int = 0


class DashboardInventoryPoint(BaseModel):
    branch_name: str
    product_name: str
    variant_sku: str
    quantity: int = 0
    reserved_quantity: int = 0
    available_quantity: int = 0


class DashboardResponse(BaseModel):
    filters: DashboardQuery = Field(default_factory=DashboardQuery)
    summary: DashboardSummary
    sales_series: list[DashboardSeriesPoint]
    movement_series: list[DashboardMovementPoint]
    branch_kpis: list[DashboardBranchKpi]
    top_products: list[DashboardProductKpi]
    low_stock: list[DashboardInventoryPoint]
