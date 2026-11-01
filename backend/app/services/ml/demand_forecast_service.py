"""Weekly, tenant-scoped demand regression with chronological evaluation."""
from datetime import date, datetime, timedelta
from math import ceil
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
        if real:
            # Fill gaps at the store's own scale, not the generator's ~100 units/week.
            scale = (sum(real.values()) / len(real)) / (sum(combined.values()) / len(combined))
            combined = {day: value * scale for day, value in combined.items()}
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
        forecast.append({'week': week.strftime('%G-W%V'), 'week_start': week.isoformat(), 'predicted_units': round(lag, 2),
                         'confidence_lower': round(max(0, lag - margin), 2), 'confidence_upper': round(lag + margin, 2)})
    return {'model_type': 'Supervised Regression',
            'evaluation_metrics': {'r2_score': round(r2, 6), 'mse': round(mse, 6), 'test_samples': len(y) - split},
            'forecast': forecast, 'data_source': source_metadata(len(real), synthetic_count),
            'recent_weekly_average': round(float(np.mean([v for _, v in points[-4:]])), 2)}


# [CU08 - Secuencia: Paso 3.2] report_routes invoca predict_demand(tenant_id, request) sobre la entidad Venta
# [CU08 - Secuencia: Paso 3.3] Venta retorna predict_demand(tenant_id, request): dict a report_routes
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
    sales = db.query(Sale.created_at, SaleItem.quantity, SaleItem.product_id, SaleItem.product_name).join(SaleItem, SaleItem.sale_id == Sale.id).filter(
        Sale.tenant_id == tenant_id, Sale.status == 'completed', Sale.payment_status == 'paid',
        Sale.created_at >= start, Sale.created_at < until)
    orders = db.query(Order.created_at, OrderItem.quantity, OrderItem.product_id, OrderItem.product_name).join(OrderItem, OrderItem.order_id == Order.id).filter(
        Order.tenant_id == tenant_id, Order.status == 'paid', Order.payment_status == 'paid',
        Order.created_at >= start, Order.created_at < until)
    if request.branch_id:
        sales = sales.filter(Sale.branch_id == request.branch_id)
        orders = orders.filter(Order.pickup_branch_id == request.branch_id)
    history: dict[date, float] = {}
    recent: dict = {}  # product_id -> [name, units in the last 8 weeks]
    for query in (sales, orders):
        for created_at, quantity, product_id, product_name in query.all():
            day = created_at.date()
            week = day - timedelta(days=day.weekday())
            history[week] = history.get(week, 0) + quantity
            if week >= end - timedelta(weeks=8):
                recent.setdefault(product_id, [product_name, 0])[1] += quantity
    result = forecast_from_history(history, request.target_period_weeks, today=today)

    # Split the total forecast by each product's share of the last 8 weeks (top-down forecasting).
    from sqlalchemy import func
    from app.models.inventory import Inventory
    from app.models.product_variant import ProductVariant

    total_recent = sum(units for _, units in recent.values())
    total_forecast = sum(point['predicted_units'] for point in result['forecast'])
    stock = db.query(ProductVariant.product_id, func.sum(Inventory.quantity - Inventory.reserved_quantity)).join(
        Inventory, Inventory.variant_id == ProductVariant.id).filter(Inventory.tenant_id == tenant_id)
    if request.branch_id:
        stock = stock.filter(Inventory.branch_id == request.branch_id)
    available = {pid: max(0, int(units or 0)) for pid, units in stock.group_by(ProductVariant.product_id).all()}
    products = []
    for product_id, (name, units) in recent.items():
        predicted = total_forecast * units / (total_recent or 1)
        have = available.get(product_id, 0)
        products.append({'product_id': str(product_id), 'product_name': name, 'predicted_units': round(predicted, 1),
                         'available_stock': have, 'suggested_restock': max(0, ceil(predicted - have))})
    products.sort(key=lambda row: (-row['suggested_restock'], -row['predicted_units']))
    result['products'] = products[:10]
    return result
