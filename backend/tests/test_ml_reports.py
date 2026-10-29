"""Deterministic CU8 model tests; no credentials or database required."""
from datetime import date
from math import isfinite

import pytest
from pydantic import ValidationError


def test_forecast_is_reproducible_with_holdout_metrics_and_bounded_horizon():
    from app.services.ml.demand_forecast_service import forecast_from_history

    history = {date(2026, 1, 5): 125, date(2026, 1, 12): 130}
    first = forecast_from_history(history, 4, today=date(2026, 1, 19))
    assert first == forecast_from_history(history, 4, today=date(2026, 1, 19))
    assert len(first['forecast']) == 4
    assert first['data_source']['real_samples'] == 2
    assert first['data_source']['synthetic_samples'] > 0
    assert first['evaluation_metrics']['mse'] >= 0
    assert isfinite(first['evaluation_metrics']['r2_score'])
    for point in first['forecast']:
        assert 0 <= point['confidence_lower'] <= point['predicted_units'] <= point['confidence_upper']
    assert first['forecast'][0]['week'] == '2026-W04'


@pytest.mark.parametrize('weeks', [0, 13])
def test_forecast_horizon_rejected(weeks):
    from app.schemas.report_schema import DemandForecastRequest
    with pytest.raises(ValidationError):
        DemandForecastRequest(target_period_weeks=weeks)


def test_explicit_synthetic_services_train_without_a_database():
    from uuid import uuid4
    from app.schemas.report_schema import DemandForecastRequest
    from app.services.ml.demand_forecast_service import predict_demand
    from app.services.ml.customer_segmentation_service import customer_clusters

    tenant = uuid4()
    request = DemandForecastRequest(use_synthetic_data=True, target_period_weeks=2)
    forecast = predict_demand(None, tenant, request)
    assert forecast == predict_demand(None, tenant, request)
    assert len(forecast['forecast']) == 2
    assert forecast['evaluation_metrics']['test_samples'] > 0
    assert forecast['evaluation_metrics']['mse'] >= 0
    assert isfinite(forecast['evaluation_metrics']['r2_score'])
    clusters = customer_clusters(None, tenant, use_synthetic_data=True)
    assert clusters == customer_clusters(None, tenant, use_synthetic_data=True)
    assert -1 <= clusters['evaluation_metrics']['silhouette_score'] <= 1
    assert clusters['clusters_count'] == 3
    for result in [forecast, clusters]:
        assert result['data_source']['mode'] == 'synthetic'
        assert result['data_source']['real_samples'] == 0
        assert result['data_source']['synthetic_samples'] > 0
    assert sum(s['real_customers'] for s in clusters['segments']) == 0
    assert sum(s['size'] for s in clusters['segments']) == clusters['data_source']['synthetic_samples']


def test_synthetic_only_results_are_explicitly_labeled():
    from app.services.ml.demand_forecast_service import forecast_from_history
    result = forecast_from_history({}, 1, today=date(2026, 1, 19))
    assert result['data_source']['mode'] == 'synthetic'
    assert result['data_source']['real_samples'] == 0
    assert 'sintétic' in result['data_source']['notice']


def test_segmentation_has_three_clusters_and_valid_quality_score():
    from app.services.ml.customer_segmentation_service import segment_customers
    customers = [(7, 12, 2400), (120, 1, 70)]
    result = segment_customers(customers)
    assert result == segment_customers(customers)
    assert result['clusters_count'] == 3
    assert -1 <= result['evaluation_metrics']['silhouette_score'] <= 1
    assert len({row['name'] for row in result['segments']}) == 3
    assert sum(row['size'] for row in result['segments']) == result['data_source']['real_samples'] + result['data_source']['synthetic_samples']
    assert result['data_source']['real_samples'] == 2
    assert sum(row['real_customers'] for row in result['segments']) == 2
    assert all(row['avg_spend'] >= 0 for row in result['segments'])


def test_segmentation_does_not_need_synthetic_data_with_sufficient_real_customers():
    from app.services.ml.customer_segmentation_service import segment_customers
    customers = [(i * 3, (i % 12) + 1, float((i % 7 + 1) * 100)) for i in range(40)]
    result = segment_customers(customers)
    assert result['data_source']['mode'] == 'real'
    assert result['data_source']['synthetic_samples'] == 0


def test_forecast_real_history_metrics_are_not_claimed_as_synthetic_validation():
    from datetime import timedelta
    from app.services.ml.demand_forecast_service import forecast_from_history
    today = date(2026, 1, 19)
    history = {today - timedelta(weeks=i): 100 + i % 6 for i in range(1, 65)}
    result = forecast_from_history(history, 12, today=today)
    assert len(result['forecast']) == 12
    assert result['data_source']['mode'] == 'real'
    assert result['data_source']['synthetic_samples'] == 0
    assert result['evaluation_metrics']['test_samples'] >= 2
