import pytest
from pydantic import ValidationError

from app.schemas.report_schema import NaturalReportRequest


@pytest.mark.parametrize("query", ["", "x" * 501])
def test_natural_report_request_limits_query_length(query):
    with pytest.raises(ValidationError):
        NaturalReportRequest(query=query)


def test_natural_report_request_accepts_a_spanish_sentence():
    assert NaturalReportRequest(query="ingresos por mes este año").query == "ingresos por mes este año"
