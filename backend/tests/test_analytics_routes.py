"""CU08 rutas: /reports/query interpreta localmente (sin IA) y /reports/analytics ejecuta la especificación.
Empresa propia: sucursales A1/A2; la empresa ajena (B1, "Product 1 active", "Category 1") nunca aparece."""
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_employee_authorization import headers
from test_marketplace_transactions import call, market  # noqa: F401 (shared fixture)

ENGINEER_PHRASE = "Mostrar los 10 productos más vendidos durante los últimos 3 meses agrupados por sucursal"
NOT_UNDERSTOOD = ("No entendí la consulta. Prueba con: «top 10 productos más vendidos de los últimos 3 meses "
                  "por sucursal», «ingresos por mes este año», «ventas online vs tienda de esta semana».")
LA_PAZ = timezone(timedelta(hours=-4))


@pytest.fixture
def reports_api(api):
    from app.routes import report_routes
    api.app.include_router(report_routes.router, prefix="/api")
    return api


@pytest.fixture
def sold(api_db, market):
    """Ventas de hace 2 días: A1 vende 3, A2 vende 5 y la empresa ajena (B1) vende 8 del mismo modo."""
    from app.models.sale import Sale
    from app.models.sale_item import SaleItem

    when = datetime.combine(date.today() - timedelta(days=2), datetime.min.time().replace(hour=12), LA_PAZ)
    for index, group, qty in ((0, market.own, 3), (1, market.own, 5), (2, market.foreign, 8)):
        cashier = market.staff[index, "cajero"]
        api_db.add(Sale(tenant_id=cashier.tenant_id, branch_id=cashier.branch_id, user_id=cashier.id,
                        payment_method="cash", total_amount=qty * 25, created_at=when,
                        items=[SaleItem(variant_id=group.variant.id, product_id=group.product.id,
                                        product_name="snapshot", variant_sku=group.variant.sku,
                                        quantity=qty, unit_price=25, line_total=qty * 25)]))
    api_db.commit()
    return market


def spec(**extra):
    return {"metric": "units", "group_by": ["branch"], "period": {"preset": "last_n_days", "n": 30}, **extra}


def test_engineer_phrase_is_resolved_without_ai(reports_api, market):
    admin = market.staff[0, "administrador"]
    data = call(reports_api, admin, "POST", "/reports/query", expected_message="Reporte interpretado exitosamente",
                json={"query": ENGINEER_PHRASE})
    assert data["spec"]["group_by"] == ["branch", "product"] and data["spec"]["top_n"] == 10
    assert data["spec"]["period"] == {"preset": "last_n_months", "n": 3, "from_date": None, "to_date": None}
    assert data["spec"]["branch_ids"] == []
    assert data["interpretation"].startswith("Top 10 productos por unidades vendidas")
    assert f"al {date.today():%d/%m/%Y}" in data["interpretation"]
    assert "report" not in data and "rows" not in data  # ya no ejecuta el reporte


def test_unknown_query_returns_examples_without_ai(reports_api, market):
    result = reports_api.post("/api/reports/query", headers=headers(market.staff[0, "administrador"]),
                              json={"query": "haz un poema"})
    assert result.status_code == 422, result.text
    assert result.json() == {"statusCode": 422, "message": NOT_UNDERSTOOD, "error": NOT_UNDERSTOOD}


@pytest.mark.parametrize("query", ["", "x" * 501])
def test_query_length_is_validated(reports_api, market, query):
    result = reports_api.post("/api/reports/query", headers=headers(market.staff[0, "administrador"]),
                              json={"query": query})
    assert result.status_code == 422, result.text


def test_reports_never_import_gemini():
    import app.services.natural_report_service as service
    source = open(service.__file__, encoding="utf-8").read().lower()
    assert "genai" not in source and "gemini" not in source


def test_query_requires_ai_text_reports_plan(reports_api, api_db, market):
    from app.models.subscription_plan import SubscriptionPlan
    from app.services.subscription_service import create_or_update_tenant_subscription
    api_db.add(SubscriptionPlan(id="cu8_basic", name="Sin IA", slug="cu8-basic", features=["standard_reports"]))
    api_db.flush()
    create_or_update_tenant_subscription(api_db, market.own.tenant.id, "cu8_basic")
    api_db.commit()
    admin = market.staff[0, "administrador"]
    result = reports_api.post("/api/reports/query", headers=headers(admin), json={"query": ENGINEER_PHRASE})
    assert result.status_code == 403, result.text
    assert "no incluye reportes con Inteligencia Artificial" in result.json()["message"]
    # /analytics no depende del plan de IA
    call(reports_api, admin, "POST", "/reports/analytics", json=spec())


def test_query_is_denied_without_reports_permission(reports_api, market):
    result = reports_api.post("/api/reports/query", headers=headers(market.staff[0, "cajero"]),
                              json={"query": ENGINEER_PHRASE})
    assert result.status_code == 403, result.text


def test_analytics_route_runs_the_spec(reports_api, sold):
    admin = sold.staff[0, "administrador"]
    data = call(reports_api, admin, "POST", "/reports/analytics", expected_message="Reporte generado exitosamente",
                json=spec())
    assert data["rows"] == [{"branch": "A1", "units": 3}, {"branch": "A2", "units": 5}]
    assert data["totals"]["units"] == 8
    assert data["title"] == "Unidades vendidas por sucursal"


def test_analytics_rejects_an_invalid_period(reports_api, market):
    message = "Indica las fechas del período"
    result = reports_api.post("/api/reports/analytics", headers=headers(market.staff[0, "administrador"]),
                              json=spec(period={"preset": "custom"}))
    assert result.status_code == 422, result.text
    assert result.json() == {"statusCode": 422, "message": message, "error": message}


def test_manager_is_forced_to_own_branch(reports_api, sold):
    manager = sold.staff[0, "encargado"]
    data = call(reports_api, manager, "POST", "/reports/analytics",
                json=spec(branch_ids=[str(sold.branches[1].id)]))
    assert {r["branch"] for r in data["rows"]} <= {"A1"}
    assert data["rows"] == [{"branch": "A1", "units": 3}]
    interpreted = call(reports_api, manager, "POST", "/reports/query", json={"query": "ventas por sucursal A2"})
    assert interpreted["spec"]["branch_ids"] == [str(sold.branches[0].id)]


def test_manager_without_branch_is_rejected(reports_api, api_db, market):
    manager = market.staff[0, "encargado"]
    manager.branch_id = None
    api_db.commit()
    for path, body in (("/reports/analytics", spec()), ("/reports/query", {"query": ENGINEER_PHRASE})):
        result = reports_api.post("/api" + path, headers=headers(manager), json=body)
        assert result.status_code == 403, result.text


def test_query_never_matches_foreign_catalog_names(reports_api, sold):
    """Los nombres de la empresa ajena no están en el catálogo: no se convierten en filtros."""
    admin = sold.staff[0, "administrador"]
    own = call(reports_api, admin, "POST", "/reports/query", json={"query": "ventas por mes de Product 0 active"})
    assert own["spec"]["product_ids"] == [str(sold.own.product.id)]
    # "categoria <nombre que no está en el catálogo>": regla de oro, no se responde sin ese filtro (422)
    foreign = reports_api.post("/api/reports/query", headers=headers(admin),
                               json={"query": "ventas por mes de Product 1 active en B1 categoria Category 1"})
    assert foreign.status_code == 422, foreign.text
    assert foreign.json() == {"statusCode": 422, "message": NOT_UNDERSTOOD, "error": NOT_UNDERSTOOD}
    for item in (sold.foreign.product, sold.foreign.category, sold.branches[2]):
        assert str(item.id) not in foreign.text


@pytest.mark.parametrize("field,label", [("branch_ids", "sucursal"), ("product_ids", "producto"),
                                         ("category_ids", "categoría")])
def test_analytics_rejects_foreign_ids(reports_api, sold, field, label):
    item = {"branch_ids": sold.branches[2], "product_ids": sold.foreign.product,
            "category_ids": sold.foreign.category}[field]
    for target in (item.id, uuid4()):
        result = reports_api.post("/api/reports/analytics", headers=headers(sold.staff[0, "administrador"]),
                                  json=spec(**{field: [str(target)]}))
        assert result.status_code == 422, result.text
        message = f"No se encontró en el catálogo: {label} {target}"
        assert result.json() == {"statusCode": 422, "message": message, "error": message}


def test_analytics_never_returns_foreign_rows(reports_api, sold):
    data = call(reports_api, sold.staff[0, "administrador"], "POST", "/reports/analytics",
                json=spec(group_by=["product"]))
    assert data["rows"] == [{"product": sold.own.product.name, "units": 8}]


RANGE = "Las fechas están fuera de un rango razonable"


@pytest.mark.parametrize("period,compare", [
    ({"preset": "custom", "from_date": "0001-01-01", "to_date": "0001-01-05"}, True),
    ({"preset": "custom", "from_date": "0001-01-01", "to_date": "0001-01-05"}, False),
    ({"preset": "custom", "from_date": "1999-12-31", "to_date": "2000-01-05"}, False),
    # the previous period (1999-12-26..1999-12-31) would start before 2000
    ({"preset": "custom", "from_date": "2000-01-01", "to_date": "2000-01-06"}, True),
])
def test_analytics_rejects_unreasonable_dates(reports_api, market, period, compare):
    result = reports_api.post("/api/reports/analytics", headers=headers(market.staff[0, "administrador"]),
                              json=spec(period=period, compare_previous=compare))
    assert result.status_code == 422, result.text
    assert result.json() == {"statusCode": 422, "message": RANGE, "error": RANGE}


def test_query_rejects_unreasonable_dates(reports_api, market):
    result = reports_api.post("/api/reports/query", headers=headers(market.staff[0, "administrador"]),
                              json={"query": "ventas del 01/01/0001 al 05/01/0001 vs"})
    assert result.status_code == 422, result.text
    assert result.json()["message"] == RANGE


def test_analytics_accepts_edge_and_future_dates(reports_api, market):
    admin = market.staff[0, "administrador"]
    # boundary: the previous period is exactly 2000-01-01..2000-01-06
    data = call(reports_api, admin, "POST", "/reports/analytics", json=spec(
        period={"preset": "custom", "from_date": "2000-01-07", "to_date": "2000-01-12"}, compare_previous=True))
    assert data["previous_totals"] == {"units": 0, "revenue": 0.0, "orders": 0, "avg_ticket": 0.0}
    start = date(date.today().year, 1, 1).isoformat()
    data = call(reports_api, admin, "POST", "/reports/analytics", json=spec(
        period={"preset": "custom", "from_date": start, "to_date": "9999-12-31"}, compare_previous=True))
    assert data["period"]["to_date"] == date.today().isoformat()  # future end clamped to today
    data = call(reports_api, admin, "POST", "/reports/analytics", json=spec(
        period={"preset": "custom", "from_date": "9999-12-31", "to_date": "9999-12-31"}, compare_previous=True))
    assert data["period"]["from_date"] == date.today().isoformat()


def test_catalog_skips_names_that_normalize_to_nothing(api_db, market):
    from app.models.product import Product
    from app.services.natural_report_service import _catalog
    api_db.add(Product(name="¡¿...?!", tenant_id=market.own.tenant.id, category_id=market.own.category.id))
    api_db.commit()
    catalog = _catalog(api_db, market.own.tenant.id)
    assert "" not in catalog.products and "" not in catalog.branches and "" not in catalog.categories


def test_catalog_with_punctuation_only_name_does_not_filter_every_query(reports_api, api_db, market):
    from app.models.product import Product
    api_db.add(Product(name="---", tenant_id=market.own.tenant.id, category_id=market.own.category.id))
    api_db.commit()
    data = call(reports_api, market.staff[0, "administrador"], "POST", "/reports/query",
                json={"query": "ingresos por mes este año /"})  # "/" survives normalize: "" would match there
    assert data["spec"]["product_ids"] == []


@pytest.mark.parametrize("field", ["branch_ids", "product_ids", "category_ids"])
def test_filter_lists_are_capped_at_50(field):
    from pydantic import ValidationError
    from app.schemas.analytics_schema import AnalyticsQuery
    base = {"period": {"preset": "today"}}
    assert len(getattr(AnalyticsQuery(**base, **{field: [uuid4() for _ in range(50)]}), field)) == 50
    with pytest.raises(ValidationError):
        AnalyticsQuery(**base, **{field: [uuid4() for _ in range(51)]})
