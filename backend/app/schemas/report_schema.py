from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.order_schema import PaymentMethodEnum, PaymentStatusEnum
from app.schemas.sales_schema import SaleStatusEnum
from app.schemas.inventory_schema import InventoryMovementTypeEnum


class ReportExportFormatEnum(str, Enum):
    csv = "csv"


class ReportSummary(BaseModel):
    total_orders: int = 0
    total_sales: Decimal = Decimal("0.00")
    total_units: int = 0
    average_ticket: Decimal = Decimal("0.00")


class SalesReportRow(BaseModel):
    branch_id: UUID
    branch_name: str
    product_id: UUID
    product_name: str
    variant_id: UUID
    variant_sku: str
    quantity_sold: int
    gross_sales: Decimal
    payment_method: PaymentMethodEnum | None = None
    payment_status: PaymentStatusEnum | None = None
    sale_status: SaleStatusEnum | None = None


class InventoryReportRow(BaseModel):
    branch_id: UUID
    branch_name: str
    product_id: UUID
    product_name: str
    variant_id: UUID
    variant_sku: str
    quantity: int
    reserved_quantity: int
    available_quantity: int


class MovementReportRow(BaseModel):
    branch_id: UUID
    branch_name: str
    product_id: UUID
    product_name: str
    variant_id: UUID
    variant_sku: str
    movement_type: InventoryMovementTypeEnum
    quantity: int
    movements_count: int


class ReportQuery(BaseModel):
    branch_id: UUID | None = None
    product_id: UUID | None = None
    variant_id: UUID | None = None
    from_date: date | None = None
    to_date: date | None = None
    q: str | None = None


class ReportExportMeta(BaseModel):
    report_type: str
    generated_at: datetime
    filters: ReportQuery = Field(default_factory=ReportQuery)
