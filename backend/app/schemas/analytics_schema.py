from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

Metric = Literal["units", "revenue", "orders", "avg_ticket", "customers"]
Dimension = Literal[
    "product", "variant", "category", "branch", "size", "color",
    "channel", "payment_method", "customer", "day", "week", "month",
]
TIME_DIMENSIONS = {"day", "week", "month"}


class PeriodSpec(BaseModel):
    preset: Literal[
        "today", "yesterday", "this_week", "last_week", "last_n_days", "this_month",
        "last_month", "last_n_months", "this_quarter", "last_quarter", "this_year", "last_year", "custom",
    ] = "last_n_days"
    n: int | None = Field(None, ge=1, le=36)
    from_date: date | None = None
    to_date: date | None = None


class AnalyticsQuery(BaseModel):
    # Non-sales kinds ignore metric, group_by, top_n, order and channel (they still validate).
    kind: Literal["sales", "inventory", "critical_stock", "movements"] = "sales"
    metric: Metric = "units"
    group_by: list[Dimension] = Field(default_factory=lambda: ["product"], max_length=2)
    top_n: int | None = Field(None, ge=1, le=50)
    order: Literal["desc", "asc"] = "desc"
    period: PeriodSpec
    branch_ids: list[UUID] = Field(default_factory=list, max_length=50)
    product_ids: list[UUID] = Field(default_factory=list, max_length=50)
    category_ids: list[UUID] = Field(default_factory=list, max_length=50)
    channel: Literal["all", "store", "online"] = "all"
    payment_methods: list[Literal["cash", "card", "qr", "wallet"]] = Field(default_factory=list, max_length=4)
    compare_previous: bool = False
    chart: Literal["bar", "line", "donut", "table"] | None = None

    @model_validator(mode="after")
    def _check_dimensions(self):
        if len(set(self.group_by)) != len(self.group_by):
            raise ValueError("No se puede repetir una dimensión")
        if len(TIME_DIMENSIONS & set(self.group_by)) > 1:
            raise ValueError("Solo se puede agrupar por un período de tiempo")
        return self


class AnalyticsResult(BaseModel):
    title: str
    period: dict  # from_date, to_date, label
    columns: list[dict]  # key, label, type: "text" | "number" | "money"
    rows: list[dict]
    totals: dict
    previous_totals: dict | None = None
    delta_pct: dict | None = None
    chart: str
    message: str | None = None
