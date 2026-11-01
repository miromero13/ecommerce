"""CU08 exportación profesional: PDF/Excel del resultado analítico (servicio puro + ruta)."""
import re
from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook
PdfReader = pytest.importorskip("pypdf").PdfReader

from app.schemas.analytics_schema import AnalyticsResult
from app.services.report_export_service import analytics_to_excel, analytics_to_pdf
from test_analytics_routes import reports_api, sold, spec  # noqa: F401 (shared fixtures)
from test_catalog_tenant_isolation import catalog  # noqa: F401
from test_marketplace_transactions import market  # noqa: F401
from test_employee_authorization import headers


def result(rows=None, dims=1, columns=None, **extra):
    columns = columns or [{"key": "branch", "label": "Sucursal", "type": "text"}]
    if dims == 2:
        columns = [*columns, {"key": "product", "label": "Producto", "type": "text"}]
    if not any(c["type"] != "text" for c in columns):
        columns = [*columns, {"key": "revenue", "label": "Ingresos (Bs.)", "type": "money"}]
    rows = [{"branch": "A1", "product": "Polera", "revenue": 1234.5}] if rows is None else rows
    base = dict(title="Top 10 productos por sucursal", period={"label": "Últimos 30 días"}, columns=columns,
                rows=rows, totals={"units": 10, "revenue": 1234.5, "orders": 3, "avg_ticket": 411.5},
                chart="bar")
    return AnalyticsResult(**{**base, **extra})


def text_of(pdf: bytes) -> str:
    return "\n".join(page.extract_text() for page in PdfReader(BytesIO(pdf)).pages)


def test_pdf_has_title_period_and_pages():
    pdf = analytics_to_pdf(result(delta_pct={"units": 12.5, "revenue": -3.0}), "Mi Empresa", "Ana")
    text = text_of(pdf)
    assert pdf.startswith(b"%PDF-") and "Top 10" in text and "Página 1 de 1" in text
    assert "Mi Empresa" in text and "Últimos 30 días" in text and "por Ana" in text
    assert "1,234.50 Bs." in text and "+12,5 %" in text and "-3,0 %" in text


def test_pdf_is_valid_when_empty_or_markup_like():
    empty = analytics_to_pdf(result(rows=[], message="Sin ventas en el período"), "E", "U")
    assert "Sin ventas en el período" in text_of(empty)
    odd = analytics_to_pdf(result(rows=[{"branch": "<b>&</b> <x", "revenue": 1}], title="A<B&C"), "E&Co", "U")
    assert "<b>&</b> <x" in text_of(odd)


def test_pdf_repeats_header_and_paginates_with_two_dimensions():
    rows = [{"branch": f"S{i // 60}", "product": f"P{i}", "revenue": i} for i in range(130)]
    text = text_of(analytics_to_pdf(result(rows=rows, dims=2), "E", "U"))
    assert re.search(r"Página 3 de \d+", text) and text.count("Subtotal") == 3
    assert text.count("Ingresos (Bs.)") >= 4  # header repeated on continuation pages


def test_excel_has_header_block_subtotals_and_number_formats():
    rows = [{"branch": "A1", "product": "Polera", "revenue": 10.5}, {"branch": "A1", "product": "Gorra", "revenue": 4},
            {"branch": "A2", "product": "Polera", "revenue": 2}]
    ws = load_workbook(BytesIO(analytics_to_excel(result(rows=rows, dims=2), "Mi Empresa", "Ana"))).active
    assert ws["A1"].value == "Top 10 productos por sucursal" and ws["A2"].value == "Mi Empresa"
    assert "Últimos 30 días" in ws["A3"].value and "por Ana" in ws["A4"].value
    assert [c.value for c in ws[6]] == ["Sucursal", "Producto", "Ingresos (Bs.)"]
    assert ws.freeze_panes == "A7" and ws.auto_filter.ref == "A6:C11"
    assert ws["C7"].value == 10.5 and ws["C7"].number_format == "#,##0.00"
    subtotal = ws[9]
    assert subtotal[0].value == "Subtotal" and subtotal[2].value == 14.5 and subtotal[0].font.bold
    assert ws["C10"].value == 2 and ws["A11"].value == "Subtotal" and ws["C11"].font.bold


def test_excel_counts_use_integer_format_and_empty_workbook_is_valid():
    cols = [{"key": "branch", "label": "Producto", "type": "text"},
            {"key": "units", "label": "Unidades", "type": "number"}]
    ws = load_workbook(BytesIO(analytics_to_excel(
        result(columns=cols, rows=[{"branch": "x", "units": 5}]), "E", "U"))).active
    assert ws["B7"].number_format == "#,##0"
    empty = load_workbook(BytesIO(analytics_to_excel(result(rows=[], message="Nada"), "E", "U"))).active
    assert empty["A6"].value == "Sucursal" and empty["A7"].value == "Nada"


def test_excel_never_executes_formulas():
    evil = '=HYPERLINK("http://x","clic")'
    data = analytics_to_excel(result(rows=[{"branch": evil, "revenue": 1}], title="=1+1"), "=cmd", "+u")
    ws = load_workbook(BytesIO(data)).active
    for ref in ("A1", "A2", "A7"):
        assert ws[ref].data_type == "s"
    assert ws["A7"].value == evil


def test_export_route_returns_file_with_name(reports_api, sold):
    admin = sold.staff[0, "administrador"]
    xlsx = reports_api.post("/api/reports/analytics/export?format=excel", headers=headers(admin), json=spec())
    assert xlsx.status_code == 200, xlsx.text
    assert xlsx.headers["content-disposition"] == (
        f'attachment; filename="reporte-unidades-vendidas-por-sucursal-{date.today():%Y-%m-%d}.xlsx"')
    ws = load_workbook(BytesIO(xlsx.content)).active
    assert [ws["A7"].value, ws["B7"].value, ws["A8"].value, ws["B8"].value] == ["A1", 3, "A2", 5]
    assert admin.name in ws["A4"].value and ws["A2"].value == sold.own.tenant.name
    pdf = reports_api.post("/api/reports/analytics/export?format=pdf", headers=headers(admin), json=spec())
    assert pdf.headers["content-type"] == "application/pdf" and pdf.content.startswith(b"%PDF-")
    assert ".pdf" in pdf.headers["content-disposition"]


def test_export_rejects_bad_format_and_scopes_manager(reports_api, sold):
    admin, manager = sold.staff[0, "administrador"], sold.staff[0, "encargado"]
    url = "/api/reports/analytics/export"
    assert reports_api.post(url + "?format=csv", headers=headers(admin), json=spec()).status_code == 422
    assert reports_api.post(url, headers=headers(admin), json=spec()).status_code == 422
    out = reports_api.post(url + "?format=excel", headers=headers(manager),
                           json=spec(branch_ids=[str(sold.branches[1].id)]))
    ws = load_workbook(BytesIO(out.content)).active
    assert [ws["A7"].value, ws["B7"].value, ws["A8"].value] == ["A1", 3, None]
    cashier = reports_api.post(url + "?format=pdf", headers=headers(sold.staff[0, "cajero"]), json=spec())
    assert cashier.status_code == 403
