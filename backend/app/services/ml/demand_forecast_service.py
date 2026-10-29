"""Weekly, tenant-scoped demand regression with chronological evaluation."""
from datetime import date, datetime, timedelta
from uuid import UUID

import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

from app.schemas.report_schema import DemandForecastRequest
from app.services.ml.synthetic_data_generator import source_metadata, synthetic_weeks


def _features(week: date, lag: float, index: int) -> list[float]:
    angle = 2 * np.pi * week.isocalendar().week / 52
    return [index, week.month, np.sin(angle), np.cos(angle), lag]


def forecast_from_history(history: dict[date, float], weeks: int, *, today: date | None = None) -> dict:
    if not 1 <= weeks <= 12:
        raise ValueError('El horizonte debe estar entre 1 y 12 semanas')
    today = today or date.today()
    end = today - timedelta(days=today.weekday())
    real = {day: float(value) for day, value in history.items() if end - timedelta(weeks=104) <= day < end}
    if len(real) < 26:
        count = max(64, (end - min(real)).days // 7) if real else 64
        combined = synthetic_weeks(end, count)
        combined.update(real)
        synthetic_count = len(set(combined) - set(real))
    else:
        start = min(real)
        combined = {start + timedelta(weeks=i): real.get(start + timedelta(weeks=i), 0.0)
                    for i in range((end - start).days // 7)}
        synthetic_count = 0
    points = sorted(combined.items())
    x = np.asarray([_features(day, points[i - 1][1], i) for i, (day, _) in enumerate(points) if i])
    y = np.asarray([value for _, value in points[1:]])
    split = int(len(y) * 0.8)
    model = LinearRegression().fit(x[:split], y[:split])
    predicted = np.maximum(0, model.predict(x[split:]))
    mse = float(mean_squared_error(y[split:], predicted))
    r2 = float(r2_score(y[split:], predicted))
    margin = 1.96 * np.sqrt(mse)
    model.fit(x, y)
    lag = points[-1][1]
    forecast = []
    for i in range(weeks):
        week = end + timedelta(weeks=i)
        lag = max(0.0, float(model.predict([_features(week, lag, len(points) + i)])[0]))
        forecast.append({'week': week.strftime('%G-W%V'), 'predicted_units': round(lag, 2),
                         'confidence_lower': round(max(0, lag - margin), 2), 'confidence_upper': round(lag + margin, 2)})
    return {'model_type': 'Supervised Regression',
            'evaluation_metrics': {'r2_score': round(r2, 6), 'mse': round(mse, 6), 'test_samples': len(y) - split},
            'forecast': forecast, 'data_source': source_metadata(len(real), synthetic_count)}


def predict_demand(db, tenant_id: UUID, request: DemandForecastRequest) -> dict:
    if request.use_synthetic_data:
        return forecast_from_history({}, request.target_period_weeks)

    # Import database models only for the DB-backed entry point; pure training needs no settings.
    from app.models.sale import Sale
    from app.models.sale_item import SaleItem
    from app.models.order import Order
    from app.models.order_item import OrderItem

    today = date.today()
    end = today - timedelta(days=today.weekday())
    start = datetime.combine(end - timedelta(weeks=104), datetime.min.time())
    until = datetime.combine(end, datetime.min.time())
    sales = db.query(Sale.created_at, SaleItem.quantity).join(SaleItem, SaleItem.sale_id == Sale.id).filter(
        Sale.tenant_id == tenant_id, Sale.status == 'completed', Sale.payment_status == 'paid',
        Sale.created_at >= start, Sale.created_at < until)
    orders = db.query(Order.created_at, OrderItem.quantity).join(OrderItem, OrderItem.order_id == Order.id).filter(
        Order.tenant_id == tenant_id, Order.status == 'paid', Order.payment_status == 'paid',
        Order.created_at >= start, Order.created_at < until)
    if request.branch_id:
        sales = sales.filter(Sale.branch_id == request.branch_id)
        orders = orders.filter(Order.pickup_branch_id == request.branch_id)
    history: dict[date, float] = {}
    for query in (sales, orders):
        for created_at, quantity in query.all():
            day = created_at.date()
            week = day - timedelta(days=day.weekday())
            history[week] = history.get(week, 0) + quantity
    return forecast_from_history(history, request.target_period_weeks, today=today)
