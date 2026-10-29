from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from typing import Literal

from pydantic import BaseModel, Field, field_validator

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
    type: str
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


AllowedReportColumn = Literal[
    "branch_name",
    "product_name",
    "variant_sku",
    "type",
    "quantity_sold",
    "gross_sales",
    "payment_method",
    "payment_status",
    "sale_status",
    "quantity",
    "reserved_quantity",
    "available_quantity",
    "minimum_stock",
    "movement_type",
    "movements_count",
]

AllowedSalesReportColumn = Literal[
    "branch_name",
    "product_name",
    "variant_sku",
    "type",
    "quantity_sold",
    "gross_sales",
    "payment_method",
    "payment_status",
    "sale_status",
]

DEFAULT_SALES_REPORT_COLUMNS: list[AllowedSalesReportColumn] = [
    "branch_name",
    "product_name",
    "variant_sku",
    "type",
    "quantity_sold",
    "gross_sales",
    "payment_method",
    "payment_status",
    "sale_status",
]

DEFAULT_INVENTORY_REPORT_COLUMNS = [
    "branch_name", "product_name", "variant_sku", "quantity", "reserved_quantity", "available_quantity",
]
DEFAULT_MOVEMENT_REPORT_COLUMNS = [
    "branch_name", "product_name", "variant_sku", "movement_type", "quantity", "movements_count",
]


SmartReportType = Literal["sales", "inventory", "movements", "top_products", "branch_comparison", "critical_inventory"]


class DemandForecastRequest(BaseModel):
    branch_id: UUID | None = None
    target_period_weeks: int = Field(default=4, ge=1, le=12)
    use_synthetic_data: bool = False


class CustomerClustersRequest(BaseModel):
    use_synthetic_data: bool = False


class ModelDataSource(BaseModel):
    mode: Literal["real", "mixed", "synthetic"]
    real_samples: int
    synthetic_samples: int
    notice: str


class ForecastPoint(BaseModel):
    week: str
    predicted_units: float
    confidence_lower: float
    confidence_upper: float


class ForecastMetrics(BaseModel):
    r2_score: float
    mse: float
    test_samples: int


class DemandForecast(BaseModel):
    model_type: str
    evaluation_metrics: ForecastMetrics
    forecast: list[ForecastPoint]
    data_source: ModelDataSource


class CustomerSegment(BaseModel):
    cluster_id: int
    name: str
    size: int
    avg_spend: float
    real_customers: int
    synthetic_customers: int


class ClusterMetrics(BaseModel):
    silhouette_score: float


class CustomerClusters(BaseModel):
    model_type: str
    clusters_count: int
    evaluation_metrics: ClusterMetrics
    segments: list[CustomerSegment]
    data_source: ModelDataSource


class NaturalReportRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)


class NaturalReportInterpretation(BaseModel):
    report_type: SmartReportType
    format: Literal["pdf", "html", "csv"] = "pdf"
    branch_id: UUID | None = None
    product_id: UUID | None = None
    variant_id: UUID | None = None
    from_date: date | None = None
    to_date: date | None = None
    q: str | None = Field(default=None, max_length=120)
    interpretation: str = Field(min_length=1, max_length=500)
    unmatched_entity: str | None = Field(default=None, max_length=160)
    columns: list[AllowedReportColumn] = Field(default_factory=lambda: DEFAULT_SALES_REPORT_COLUMNS.copy(), min_length=1)

    @field_validator("columns")
    @classmethod
    def deduplicate_columns(cls, value: list[AllowedReportColumn]) -> list[AllowedReportColumn]:
        return list(dict.fromkeys(value))


class ReportExportMeta(BaseModel):
    report_type: str
    generated_at: datetime
    filters: ReportQuery = Field(default_factory=ReportQuery)
