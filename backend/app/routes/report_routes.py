from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, require_roles
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
    get_top_products_report,
    get_branch_comparison_report,
    get_critical_inventory_report,
)
from app.services.natural_report_service import NaturalReportError, generate_natural_report
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


@router.post("/query")
async def natural_report_route(
    request: NaturalReportRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.administrador)),
    current_tenant_id: UUID | None = Depends(get_current_tenant_id),
):
    if current_tenant_id is not None:
        if not tenant_has_feature(db, current_tenant_id, "ai_text_reports"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu plan actual no incluye reportes con Inteligencia Artificial. Actualizá tu suscripción al plan Profesional o Enterprise.",
            )

    try:
        data = await generate_natural_report(db, request.query, current_tenant_id)
    except NaturalReportError as error:
        return response(status_code=error.status_code, message=error.detail, error=error.detail)
    return response(status_code=status.HTTP_200_OK, message="Reporte interpretado exitosamente", data=data)


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


def _scoped_filters(db: Session, filters: ReportQuery, current_user: dict) -> ReportQuery:
    # Services constrain tenant data; preserve successful empty-filter queries
    # and the existing rule that an encargado cannot replace their own branch.
    if current_user.get("rol") != RolEnum.encargado.value:
        return filters

    branch_id = current_user.get("branch_id")
    if not branch_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El encargado no tiene sucursal asignada")
    try:
        manager_branch_id = UUID(branch_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="La sucursal asignada no es válida")
    return filters.model_copy(update={"branch_id": manager_branch_id})


def _smart_report(db: Session, filters: ReportQuery, current_user: dict, report_type: str):
    filters = _scoped_filters(db, filters, current_user)
    if filters.from_date and filters.to_date and filters.from_date > filters.to_date:
        raise HTTPException(status_code=422, detail="El rango de fechas no es válido")
    function, _, _ = SMART_REPORTS[report_type]
    return function(db, filters, UUID(current_user["tenant_id"]))


@router.get("/top-products")
def top_products_route(
    db: Session = Depends(get_db), filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    return response(status_code=200, message="Ranking de productos obtenido exitosamente", data=_smart_report(db, filters, current_user, "top_products"))


@router.get("/branch-comparison")
def branch_comparison_route(
    db: Session = Depends(get_db), filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    return response(status_code=200, message="Comparativa de sucursales obtenida exitosamente", data=_smart_report(db, filters, current_user, "branch_comparison"))


@router.get("/critical-inventory")
def critical_inventory_route(
    db: Session = Depends(get_db), filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
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
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    return _export_file(db, filters, current_user, type, "excel")


@router.get("/export/pdf")
def pdf_export_route(
    type: SmartReportType = Query(default="sales"),
    db: Session = Depends(get_db), filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    return _export_file(db, filters, current_user, type, "pdf")


@router.get("/sales")
async def sales_report_route(
    db: Session = Depends(get_db),
    filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    filters = _scoped_filters(db, filters, current_user)
    return response(status_code=status.HTTP_200_OK, message="Reporte de ventas obtenido exitosamente", data=get_sales_report(db, filters, UUID(current_user["tenant_id"])))


@router.get("/sales/export")
async def sales_report_export_route(
    db: Session = Depends(get_db),
    filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    filters = _scoped_filters(db, filters, current_user)
    report = get_sales_report(db, filters, UUID(current_user["tenant_id"]))
    return _csv_response(
        "sales-report.csv",
        report["rows"],
        ["branch_id", "branch_name", "product_id", "product_name", "variant_id", "variant_sku", "quantity_sold", "gross_sales", "payment_method", "payment_status", "sale_status", "type"],
    )


@router.get("/inventory")
async def inventory_report_route(
    db: Session = Depends(get_db),
    filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    filters = _scoped_filters(db, filters, current_user)
    return response(status_code=status.HTTP_200_OK, message="Reporte de inventario obtenido exitosamente", data=get_inventory_report(db, filters, UUID(current_user["tenant_id"])))


@router.get("/inventory/export")
async def inventory_report_export_route(
    db: Session = Depends(get_db),
    filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    filters = _scoped_filters(db, filters, current_user)
    report = get_inventory_report(db, filters, UUID(current_user["tenant_id"]))
    return _csv_response(
        "inventory-report.csv",
        report["rows"],
        ["branch_id", "branch_name", "product_id", "product_name", "variant_id", "variant_sku", "quantity", "reserved_quantity", "available_quantity"],
    )


@router.get("/movements")
async def movements_report_route(
    db: Session = Depends(get_db),
    filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    filters = _scoped_filters(db, filters, current_user)
    return response(status_code=status.HTTP_200_OK, message="Reporte de movimientos obtenido exitosamente", data=get_movements_report(db, filters, UUID(current_user["tenant_id"])))


@router.get("/movements/export")
async def movements_report_export_route(
    db: Session = Depends(get_db),
    filters: ReportQuery = Depends(_filters),
    current_user: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    filters = _scoped_filters(db, filters, current_user)
    report = get_movements_report(db, filters, UUID(current_user["tenant_id"]))
    return _csv_response(
        "movements-report.csv",
        report["rows"],
        ["branch_id", "branch_name", "product_id", "product_name", "variant_id", "variant_sku", "movement_type", "quantity", "movements_count"],
    )
