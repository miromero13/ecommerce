from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.schemas.report_schema import ReportQuery
from app.services.report_service import (
    export_rows_to_csv,
    get_inventory_report,
    get_movements_report,
    get_sales_report,
)


router = APIRouter(prefix="/reports", tags=["Reports"])


def _filters(
    branch_id: UUID | None = Query(default=None),
    product_id: UUID | None = Query(default=None),
    variant_id: UUID | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    q: str | None = Query(default=None),
) -> ReportQuery:
    return ReportQuery(
        branch_id=branch_id,
        product_id=product_id,
        variant_id=variant_id,
        from_date=from_date,
        to_date=to_date,
        q=q,
    )


def _csv_response(filename: str, rows: list[dict], headers: list[str]):
    content = export_rows_to_csv(rows, headers)
    return StreamingResponse(
        iter([content]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/sales")
async def sales_report_route(
    db: Session = Depends(get_db),
    filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
):
    return get_sales_report(db, filters)


@router.get("/sales/export")
async def sales_report_export_route(
    db: Session = Depends(get_db),
    filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
):
    report = get_sales_report(db, filters)
    return _csv_response(
        "sales-report.csv",
        report["rows"],
        ["branch_id", "branch_name", "product_id", "product_name", "variant_id", "variant_sku", "quantity_sold", "gross_sales", "payment_method", "payment_status", "sale_status"],
    )


@router.get("/inventory")
async def inventory_report_route(
    db: Session = Depends(get_db),
    filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
):
    return get_inventory_report(db, filters)


@router.get("/inventory/export")
async def inventory_report_export_route(
    db: Session = Depends(get_db),
    filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
):
    report = get_inventory_report(db, filters)
    return _csv_response(
        "inventory-report.csv",
        report["rows"],
        ["branch_id", "branch_name", "product_id", "product_name", "variant_id", "variant_sku", "quantity", "reserved_quantity", "available_quantity"],
    )


@router.get("/movements")
async def movements_report_route(
    db: Session = Depends(get_db),
    filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
):
    return get_movements_report(db, filters)


@router.get("/movements/export")
async def movements_report_export_route(
    db: Session = Depends(get_db),
    filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
):
    report = get_movements_report(db, filters)
    return _csv_response(
        "movements-report.csv",
        report["rows"],
        ["branch_id", "branch_name", "product_id", "product_name", "variant_id", "variant_sku", "movement_type", "quantity", "movements_count"],
    )
