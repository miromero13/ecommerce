from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.report_schema import NaturalReportInterpretation, NaturalReportRequest


def test_natural_report_contract_defaults_pdf_and_accepts_report_filters():
    branch_id = uuid4()
    payload = NaturalReportInterpretation(
        report_type="sales",
        branch_id=branch_id,
        from_date=date(2026, 8, 1),
        to_date=date(2026, 8, 31),
        interpretation="Ventas de agosto",
    )

    assert payload.format == "pdf"
    assert payload.branch_id == branch_id
    assert payload.columns == [
        "branch_name", "product_name", "variant_sku", "type", "quantity_sold",
        "gross_sales", "payment_method", "payment_status", "sale_status",
    ]


def test_natural_report_contract_accepts_selected_columns_and_removes_duplicates():
    payload = NaturalReportInterpretation(
        report_type="sales",
        columns=["branch_name", "quantity_sold", "branch_name", "sale_status"],
        interpretation="Sucursal, cantidad y estado de venta",
    )

    assert payload.columns == ["branch_name", "quantity_sold", "sale_status"]


def test_natural_report_contract_rejects_unknown_column():
    with pytest.raises(ValidationError):
        NaturalReportInterpretation(
            report_type="sales",
            columns=["branch_name", "internal_id"],
            interpretation="Columnas inválidas",
        )


def test_natural_report_contract_rejects_unknown_report_type():
    with pytest.raises(ValidationError):
        NaturalReportInterpretation(report_type="sql", interpretation="invalid")


def test_natural_report_request_limits_query_length():
    with pytest.raises(ValidationError):
        NaturalReportRequest(query="x" * 501)
