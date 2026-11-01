from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.analytics_schema import AnalyticsQuery, PeriodSpec
from app.services.analytics_service import resolve_period

TODAY = date(2026, 11, 10)


def test_resolve_period_presets():
    assert resolve_period(PeriodSpec(preset="last_n_months", n=3), TODAY) == (date(2026, 8, 11), date(2026, 11, 10))
    assert resolve_period(PeriodSpec(preset="last_month"), TODAY) == (date(2026, 10, 1), date(2026, 10, 31))
    assert resolve_period(PeriodSpec(preset="this_week"), TODAY) == (date(2026, 11, 9), date(2026, 11, 10))  # lunes
    assert resolve_period(PeriodSpec(preset="last_n_days", n=7), TODAY) == (date(2026, 11, 4), date(2026, 11, 10))


def test_resolve_period_other_presets_and_defaults():
    assert resolve_period(PeriodSpec(), TODAY) == (date(2026, 10, 12), TODAY)
    assert resolve_period(PeriodSpec(preset="last_n_months"), TODAY) == (date(2026, 10, 11), TODAY)
    assert resolve_period(PeriodSpec(preset="today"), TODAY) == (TODAY, TODAY)
    assert resolve_period(PeriodSpec(preset="yesterday"), TODAY) == (date(2026, 11, 9), date(2026, 11, 9))
    assert resolve_period(PeriodSpec(preset="this_month"), TODAY) == (date(2026, 11, 1), TODAY)
    assert resolve_period(PeriodSpec(preset="this_year"), TODAY) == (date(2026, 1, 1), TODAY)
    assert resolve_period(PeriodSpec(preset="last_month"), date(2026, 1, 15)) == (date(2025, 12, 1), date(2025, 12, 31))


def test_last_n_months_clamps_day_to_month_end():
    # 31 mar - 1 mes = 28 feb (2026 no bisiesto) -> inicio 1 mar
    assert resolve_period(PeriodSpec(preset="last_n_months", n=1), date(2026, 3, 31)) == (date(2026, 3, 1), date(2026, 3, 31))
    assert resolve_period(PeriodSpec(preset="last_n_months", n=12), date(2026, 11, 10)) == (date(2025, 11, 11), date(2026, 11, 10))


def test_custom_period():
    assert resolve_period(PeriodSpec(preset="custom", from_date=date(2026, 5, 1), to_date=date(2026, 5, 2)), TODAY) == (date(2026, 5, 1), date(2026, 5, 2))
    # fechas futuras se recortan a hoy
    assert resolve_period(PeriodSpec(preset="custom", from_date=date(2026, 11, 1), to_date=date(2027, 1, 1)), TODAY) == (date(2026, 11, 1), TODAY)
    with pytest.raises(ValueError, match="Indica las fechas del período"):
        resolve_period(PeriodSpec(preset="custom"), TODAY)


def test_custom_period_validates_order():
    with pytest.raises(ValueError, match="La fecha inicial no puede ser posterior a la final"):
        resolve_period(PeriodSpec(preset="custom", from_date=date(2026, 5, 2), to_date=date(2026, 5, 1)), TODAY)


def test_query_rejects_two_time_dimensions_and_unknown_metric():
    with pytest.raises(ValidationError, match="Solo se puede agrupar por un período de tiempo"):
        AnalyticsQuery(group_by=["month", "day"], period=PeriodSpec())
    with pytest.raises(ValidationError):
        AnalyticsQuery(metric="profit", period=PeriodSpec())


def test_query_rejects_repeated_dimensions_and_accepts_valid():
    with pytest.raises(ValidationError):
        AnalyticsQuery(group_by=["product", "product"], period=PeriodSpec())
    q = AnalyticsQuery(group_by=["product", "month"], period=PeriodSpec())
    assert q.metric == "units" and q.channel == "all" and q.order == "desc"
    assert AnalyticsQuery(period=PeriodSpec()).group_by == ["product"]
