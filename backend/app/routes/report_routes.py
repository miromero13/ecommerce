import re
import unicodedata
from datetime import date
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, require_roles, require_permission
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.schemas.report_schema import (
    CustomerClusters, CustomerClustersRequest, DemandForecast, DemandForecastRequest, NaturalReportRequest, ReportQuery, SmartReportType,
)
from app.services.report_service import (
    export_rows_to_csv,
    get_inventory_report,
    get_movements_report,
    get_sales_report,
    get_top_products_report, get_branch_comparison_report,
    get_critical_inventory_report, _customers_report,  # compact: keeps CU08 diagram line refs stable
)
from app.schemas.analytics_schema import AnalyticsQuery
from app.services.analytics_service import run_query
from app.services.natural_report_service import NaturalReportError, _validate_filters, interpret_query
from app.services.subscription_service import tenant_has_feature
from app.utils.response import response


router = APIRouter(prefix="/reports", tags=["Reports"])

SMART_REPORTS = {
    "sales": (get_sales_report, "Reporte de ventas", ["branch_name", "product_name", "variant_sku", "quantity_sold", "gross_sales"]),
    "inventory": (get_inventory_report, "Reporte de inventario", ["branch_name", "product_name", "variant_sku", "quantity", "reserved_quantity", "available_quantity"]),
    "movements": (get_movements_report, "Reporte de movimientos", ["branch_name", "product_name", "variant_sku", "movement_type", "quantity", "movements_count"]),
    "top_products": (get_top_products_report, "Top 10 productos", ["product_name", "quantity_sold", "gross_sales"]),
    "branch_comparison": (get_branch_comparison_report, "Comparativa de sucursales", ["branch_name", "quantity_sold", "gross_sales"]),
    "critical_inventory": (get_critical_inventory_report, "Inventario crítico", ["branch_name", "product_name", "variant_sku", "available_quantity", "minimum_stock"]),
    "customers": (_customers_report, "Clientes", ["customer_name", "customer_email", "orders_count", "total_spent", "last_purchase"]),
}


def _ml_tenant(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
) -> UUID:
    tenant = current_user.get("tenant_id")
    if not tenant:
        raise HTTPException(status_code=403, detail="Usuario sin empresa asociada")
    tenant_id = UUID(tenant)
    if not tenant_has_feature(db, tenant_id, "ai_ml_smart_reports"):
        raise HTTPException(status_code=403, detail="Tu plan actual no incluye reportes inteligentes con Machine Learning. Actualizá tu suscripción al plan Enterprise.")
    return tenant_id


# [CU08 - Secuencia: Paso 3.1] AdminReportsPageComponent llama a predict_demand_route() de report_routes (POST /api/reports/ml/predict-demand)
# [CU08 - Secuencia: Paso 3.4] report_routes retorna predict_demand_route(): 200 Predicción de demanda con modelo supervisado generada exitosamente a AdminReportsPageComponent
@router.post("/ml/predict-demand")
def predict_demand_route(
    request: DemandForecastRequest,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(_ml_tenant),
):
    from app.models.branch import Branch
    from app.services.ml.demand_forecast_service import predict_demand

    if request.branch_id and not db.query(Branch.id).filter(
        Branch.id == request.branch_id, Branch.tenant_id == tenant_id,
    ).first():
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    data = DemandForecast.model_validate(predict_demand(db, tenant_id, request)).model_dump()
    return response(status_code=200, message="Predicción de demanda con modelo supervisado generada exitosamente", data=data)


# [CU08 - Secuencia: Paso 4.1] AdminReportsPageComponent llama a customer_clusters_route() de report_routes (POST /api/reports/ml/customer-clusters)
# [CU08 - Secuencia: Paso 4.4] report_routes retorna customer_clusters_route(): 200 Segmentación de clientes con modelo no supervisado generada a AdminReportsPageComponent
@router.post("/ml/customer-clusters")
def customer_clusters_route(
    request: CustomerClustersRequest | None = None,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(_ml_tenant),
):
    from app.services.ml.customer_segmentation_service import customer_clusters

    data = CustomerClusters.model_validate(customer_clusters(
        db, tenant_id, use_synthetic_data=request.use_synthetic_data if request else False,
    )).model_dump()
    return response(status_code=200, message="Segmentación de clientes con modelo no supervisado generada", data=data)


def _report_tenant(db: Session, tenant_id: UUID | None, feature: str | None = None) -> UUID:
    if tenant_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario sin empresa asociada")
    if feature and not tenant_has_feature(db, tenant_id, feature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu plan actual no incluye reportes con Inteligencia Artificial. Actualizá tu suscripción al plan Profesional o Enterprise.",
        )
    return tenant_id


def _scoped_spec(spec: AnalyticsQuery, current_user: dict) -> AnalyticsQuery:
    branch_id = _manager_branch_id(current_user)
    return spec if branch_id is None else spec.model_copy(update={"branch_ids": [branch_id]})


# [CU08 - Secuencia: Paso 1.1] AdminReportsPageComponent llama a natural_report_route() de report_routes (POST /api/reports/query)
# [CU08 - Secuencia: Paso 1.4] report_routes retorna natural_report_route(): 200 Reporte interpretado exitosamente a AdminReportsPageComponent
@router.post("/query")
def natural_report_route(
    request: NaturalReportRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("reports:read")),
    current_tenant_id: UUID | None = Depends(get_current_tenant_id),
):
    tenant_id = _report_tenant(db, current_tenant_id, "ai_text_reports")
    try:
        spec, interpretation, interpreted_by, warnings = interpret_query(db, tenant_id, request.query, date.today())
    except NaturalReportError as error:
        return response(status_code=error.status_code, message=error.detail, error=error.detail)
    data = {"spec": _scoped_spec(spec, current_user).model_dump(mode="json"), "interpretation": interpretation,
            "interpreted_by": interpreted_by, "warnings": warnings}
    return response(status_code=status.HTTP_200_OK, message="Reporte interpretado exitosamente", data=data)


# [CU08 - Secuencia: Paso 1.5] AdminReportsPageComponent llama a analytics_route(spec) de report_routes (POST /api/reports/analytics)
# [CU08 - Secuencia: Paso 1.10] report_routes retorna analytics_route(spec): 200 Reporte generado exitosamente a AdminReportsPageComponent
@router.post("/analytics")
def analytics_route(
    spec: AnalyticsQuery,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("reports:read")),
    current_tenant_id: UUID | None = Depends(get_current_tenant_id),
):
    tenant_id = _report_tenant(db, current_tenant_id)
    today = date.today()
    try:
        _validate_filters(db, tenant_id, spec, today)
    except NaturalReportError as error:
        return response(status_code=error.status_code, message=error.detail, error=error.detail)
    result = run_query(db, tenant_id, _scoped_spec(spec, current_user), today)
    return response(status_code=status.HTTP_200_OK, message="Reporte generado exitosamente", data=result.model_dump())


def _slug(title: str) -> str:
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")[:60].strip("-") or "analitico"


# [CU08 - Secuencia: Paso 2.1] AdminReportsPageComponent llama a analytics_export_route(spec, format) de report_routes (POST /api/reports/analytics/export)
# [CU08 - Secuencia: Paso 2.6] report_routes retorna analytics_export_route(spec, format): Response a AdminReportsPageComponent
@router.post("/analytics/export")
def analytics_export_route(
    spec: AnalyticsQuery,
    format: Literal["pdf", "excel"] = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_permission("reports:read")),
    current_tenant_id: UUID | None = Depends(get_current_tenant_id),
):
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.services.report_export_service import analytics_to_excel, analytics_to_pdf

    tenant_id = _report_tenant(db, current_tenant_id)
    today = date.today()
    try:
        _validate_filters(db, tenant_id, spec, today)
    except NaturalReportError as error:
        return response(status_code=error.status_code, message=error.detail, error=error.detail)
    result = run_query(db, tenant_id, _scoped_spec(spec, current_user), today)  # same scope as the screen
    company = db.query(Tenant.name).filter(Tenant.id == tenant_id).scalar() or ""
    author = db.query(User.name).filter(User.id == UUID(current_user["sub"])).scalar() or ""
    if format == "excel":
        content, extension = analytics_to_excel(result, company, author), "xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        content, extension, media_type = analytics_to_pdf(result, company, author), "pdf", "application/pdf"
    filename = f"reporte-{_slug(result.title)}-{today:%Y-%m-%d}.{extension}"
    return Response(content=content, media_type=media_type,
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


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


def _manager_branch_id(current_user: dict) -> UUID | None:
    # The existing rule: an encargado cannot replace their own branch.
    if current_user.get("rol") != RolEnum.encargado.value:
        return None
    branch_id = current_user.get("branch_id")
    if not branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El encargado no tiene sucursal asignada")
    try:
        return UUID(branch_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La sucursal asignada no es válida")


def _scoped_filters(db: Session, filters: ReportQuery, current_user: dict) -> ReportQuery:
    # Services constrain tenant data; preserve successful empty-filter queries.
    branch_id = _manager_branch_id(current_user)
    return filters if branch_id is None else filters.model_copy(update={"branch_id": branch_id})


def _smart_report(db: Session, filters: ReportQuery, current_user: dict, report_type: str):
    filters = _scoped_filters(db, filters, current_user)
    if filters.from_date and filters.to_date and filters.from_date > filters.to_date:
        raise HTTPException(status_code=422, detail="El rango de fechas no es válido")
    function, _, _ = SMART_REPORTS[report_type]
    return function(db, filters, UUID(current_user["tenant_id"]))


@router.get("/top-products")
def top_products_route(
    db: Session = Depends(get_db), filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_permission("reports:read")),
):
    return response(status_code=200, message="Ranking de productos obtenido exitosamente", data=_smart_report(db, filters, current_user, "top_products"))


@router.get("/branch-comparison")
def branch_comparison_route(
    db: Session = Depends(get_db), filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_permission("reports:read")),
):
    return response(status_code=200, message="Comparativa de sucursales obtenida exitosamente", data=_smart_report(db, filters, current_user, "branch_comparison"))


@router.get("/critical-inventory")
def critical_inventory_route(
    db: Session = Depends(get_db), filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_permission("reports:read")),
):
    return response(status_code=200, message="Inventario crítico obtenido exitosamente", data=_smart_report(db, filters, current_user, "critical_inventory"))


def _export_file(db: Session, filters: ReportQuery, current_user: dict, report_type: str, format: str):
    from app.services.report_export_service import to_excel, to_pdf

    report = _smart_report(db, filters, current_user, report_type)
    _, title, headers = SMART_REPORTS[report_type]
    if format == "excel":
        content, extension, media_type = to_excel(report["rows"], headers), "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        content, extension, media_type = to_pdf(title, report["rows"], headers), "pdf", "application/pdf"
    return Response(content=content, media_type=media_type,
                    headers={"Content-Disposition": f'attachment; filename="{report_type}-report.{extension}"'})


@router.get("/export/excel")
def excel_export_route(
    type: SmartReportType = Query(default="sales"),
    db: Session = Depends(get_db), filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_permission("reports:read")),
):
    return _export_file(db, filters, current_user, type, "excel")


@router.get("/export/pdf")
def pdf_export_route(
    type: SmartReportType = Query(default="sales"),
    db: Session = Depends(get_db), filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_permission("reports:read")),
):
    return _export_file(db, filters, current_user, type, "pdf")


# [CU14 - Secuencia: Paso 1.1] SalesHistoryPageComponent llama a sales_report_route() de report_routes (GET /api/reports/sales)
# [CU14 - Secuencia: Paso 1.2] report_routes retorna sales_report_route(): 200 Reporte de ventas obtenido exitosamente a SalesHistoryPageComponent
@router.get("/sales")
async def sales_report_route(
    db: Session = Depends(get_db),
    filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_permission("reports:read")),
):
    filters = _scoped_filters(db, filters, current_user)
    return response(status_code=status.HTTP_200_OK, message="Reporte de ventas obtenido exitosamente", data=get_sales_report(db, filters, UUID(current_user["tenant_id"])))


@router.get("/sales/export")
async def sales_report_export_route(
    db: Session = Depends(get_db),
    filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_permission("reports:read")),
):
    filters = _scoped_filters(db, filters, current_user)
    report = get_sales_report(db, filters, UUID(current_user["tenant_id"]))
    return _csv_response(
        "sales-report.csv",
        report["rows"],
        ["branch_id", "branch_name", "product_id", "product_name", "variant_id", "variant_sku", "quantity_sold", "gross_sales", "payment_method", "payment_status", "sale_status", "type"],
    )


# [CU14 - Secuencia: Paso 2.1] AdminInventoryPageComponent llama a inventory_report_route() de report_routes (GET /api/reports/inventory)
# [CU14 - Secuencia: Paso 2.2] report_routes retorna inventory_report_route(): 200 Reporte de inventario obtenido exitosamente a AdminInventoryPageComponent
@router.get("/inventory")
async def inventory_report_route(
    db: Session = Depends(get_db),
    filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_permission("reports:read")),
):
    filters = _scoped_filters(db, filters, current_user)
    return response(status_code=status.HTTP_200_OK, message="Reporte de inventario obtenido exitosamente", data=get_inventory_report(db, filters, UUID(current_user["tenant_id"])))


@router.get("/inventory/export")
async def inventory_report_export_route(
    db: Session = Depends(get_db),
    filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_permission("reports:read")),
):
    filters = _scoped_filters(db, filters, current_user)
    report = get_inventory_report(db, filters, UUID(current_user["tenant_id"]))
    return _csv_response(
        "inventory-report.csv",
        report["rows"],
        ["branch_id", "branch_name", "product_id", "product_name", "variant_id", "variant_sku", "quantity", "reserved_quantity", "available_quantity"],
    )


# [CU14 - Secuencia: Paso 2.3] AdminInventoryPageComponent llama a movements_report_route() de report_routes (GET /api/reports/movements)
# [CU14 - Secuencia: Paso 2.4] report_routes retorna movements_report_route(): 200 Reporte de movimientos obtenido exitosamente a AdminInventoryPageComponent
@router.get("/movements")
async def movements_report_route(
    db: Session = Depends(get_db),
    filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_permission("reports:read")),
):
    filters = _scoped_filters(db, filters, current_user)
    return response(status_code=status.HTTP_200_OK, message="Reporte de movimientos obtenido exitosamente", data=get_movements_report(db, filters, UUID(current_user["tenant_id"])))


@router.get("/movements/export")
async def movements_report_export_route(
    db: Session = Depends(get_db),
    filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_permission("reports:read")),
):
    filters = _scoped_filters(db, filters, current_user)
    report = get_movements_report(db, filters, UUID(current_user["tenant_id"]))
    return _csv_response(
        "movements-report.csv",
        report["rows"],
        ["branch_id", "branch_name", "product_id", "product_name", "variant_id", "variant_sku", "movement_type", "quantity", "movements_count"],
    )
