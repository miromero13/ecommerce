"""CU08 R2: nuevos presets, filtro de métodos de pago, clientes y tipos de reporte de inventario.
Empresa propia: sucursales A1/A2 (inventario en A1); la empresa ajena (B1) nunca aparece."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from io import BytesIO

import pytest
from openpyxl import load_workbook

from app.schemas.analytics_schema import AnalyticsQuery, PeriodSpec
from app.services.analytics_service import resolve_period
from test_analytics_engine import TODAY, at, run, shop  # noqa: F401 (shared fixtures)
from test_analytics_routes import reports_api  # noqa: F401
from test_catalog_tenant_isolation import catalog  # noqa: F401
from test_employee_authorization import headers
from test_marketplace_transactions import call, market  # noqa: F401

LA_PAZ = timezone(timedelta(hours=-4))
WEDNESDAY = date(2026, 11, 11)


def line_items(model, variant, qty, total):
    return model(variant_id=variant.id, product_id=variant.product_id, product_name="snapshot",
                 variant_sku=variant.sku, size_id=variant.size_id, color_id=variant.color_id,
                 quantity=qty, unit_price=Decimal(total) / qty, line_total=total)


# --- presets -------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("preset, today, expected", [
    ("last_week", WEDNESDAY, (date(2026, 11, 2), date(2026, 11, 8))),
    ("last_week", date(2026, 11, 9), (date(2026, 11, 2), date(2026, 11, 8))),  # lunes
    ("last_week", date(2026, 1, 1), (date(2025, 12, 22), date(2025, 12, 28))),
    ("this_quarter", WEDNESDAY, (date(2026, 10, 1), WEDNESDAY)),
    ("this_quarter", date(2026, 1, 1), (date(2026, 1, 1), date(2026, 1, 1))),
    ("this_quarter", date(2026, 6, 30), (date(2026, 4, 1), date(2026, 6, 30))),
    ("last_quarter", WEDNESDAY, (date(2026, 7, 1), date(2026, 9, 30))),
    ("last_quarter", date(2026, 2, 15), (date(2025, 10, 1), date(2025, 12, 31))),
    ("last_quarter", date(2026, 4, 1), (date(2026, 1, 1), date(2026, 3, 31))),
    ("last_year", WEDNESDAY, (date(2025, 1, 1), date(2025, 12, 31))),
    ("last_year", date(2024, 3, 1), (date(2023, 1, 1), date(2023, 12, 31))),
])
def test_new_presets(preset, today, expected):
    assert resolve_period(PeriodSpec(preset=preset), today) == expected


def test_schema_defaults_and_validation():
    q = AnalyticsQuery(period=PeriodSpec())
    assert q.kind == "sales" and q.payment_methods == [] and q.metric == "units"
    AnalyticsQuery(kind="inventory", metric="customers", group_by=["customer", "month"], top_n=3,
                   payment_methods=["cash", "card", "qr", "wallet"], period=PeriodSpec(preset="last_quarter"))
    from pydantic import ValidationError
    for bad in ({"kind": "profit"}, {"payment_methods": ["bitcoin"]},
                {"payment_methods": ["cash"] * 5}, {"kind": "inventory", "group_by": ["day", "month"]}):
        with pytest.raises(ValidationError):
            AnalyticsQuery(period=PeriodSpec(), **bad)


# --- sales engine: payment methods and customers -------------------------------------------------------------

@pytest.fixture
def paid(api_db, shop, market):
    """Store: cash 1u, qr 2u, card 4u (customer 'Other customer'); online: card 8u, wallet 16u ('Employee')."""
    from app.models.order import Order
    from app.models.order_item import OrderItem
    from app.models.sale import Sale
    from app.models.sale_item import SaleItem

    def sale(method, qty, customer=None):
        cashier = market.staff[0, "cajero"]
        api_db.add(Sale(tenant_id=cashier.tenant_id, branch_id=cashier.branch_id, user_id=cashier.id,
                        payment_method=method, total_amount=qty * 10, created_at=at(TODAY),
                        customer_id=customer.id if customer else None,
                        items=[line_items(SaleItem, shop.variant, qty, qty * 10)]))

    def order(method, qty, customer):
        api_db.add(Order(tenant_id=market.branches[0].tenant_id, user_id=customer.id,
                         pickup_branch_id=market.branches[0].id, status="paid", payment_method=method,
                         payment_status="paid", total_amount=qty * 10, created_at=at(TODAY),
                         items=[line_items(OrderItem, shop.variant, qty, qty * 10)]))

    sale("cash", 1)
    sale("qr", 2)
    sale("stripe", 4, market.other)
    order("stripe", 8, market.customer)
    order("wallet", 16, market.customer)
    # foreign company: same customer, never counted
    cashier = market.staff[2, "cajero"]
    api_db.add(Sale(tenant_id=cashier.tenant_id, branch_id=cashier.branch_id, user_id=cashier.id,
                    payment_method="cash", total_amount=320, created_at=at(TODAY), customer_id=market.customer.id,
                    items=[line_items(SaleItem, shop.foreign.variant, 32, 320)]))
    api_db.flush()
    return market


@pytest.mark.parametrize("methods, channel, units", [
    (["cash"], "all", 1), (["qr"], "all", 2), (["card"], "all", 12), (["wallet"], "all", 16),
    (["cash", "qr"], "all", 3), (["card"], "store", 4), (["card"], "online", 8),
    (["cash"], "online", 0), ([], "all", 31),
])
def test_payment_methods_filter(api_db, shop, paid, methods, channel, units):
    result = run(api_db, shop, group_by=["channel"], payment_methods=methods, channel=channel)
    assert result.totals["units"] == units
    assert sum(r["units"] for r in result.rows) == units


def test_customer_dimension_counts_only_identified_customers(api_db, shop, paid):
    result = run(api_db, shop, metric="revenue", group_by=["customer"])
    assert result.rows == [{"customer": "Employee", "revenue": Decimal("240.00")},
                           {"customer": "Other customer", "revenue": Decimal("40.00")}]
    assert result.columns[0] == {"key": "customer", "label": "Cliente", "type": "text"}
    assert result.totals["revenue"] == Decimal("280.00") and result.totals["customers"] == 2
    assert result.title == "Clientes que más compran por ingresos"


def test_customers_metric(api_db, shop, paid):
    result = run(api_db, shop, metric="customers", group_by=["channel"])
    assert result.rows == [{"channel": "En línea", "customers": 1}, {"channel": "Tienda", "customers": 1}]
    assert result.columns[-1] == {"key": "customers", "label": "Clientes", "type": "number"}
    assert result.totals["customers"] == 2 and result.totals["units"] == 28  # anonymous till sales excluded
    total = run(api_db, shop, metric="customers", group_by=[])
    assert total.rows == [{"customers": 2}] and total.title == "Clientes distintos"
    assert run(api_db, shop, metric="customers", group_by=[], channel="store", payment_methods=["cash"]).rows \
        == [{"customers": 0}]


def test_sales_without_customer_fields_keep_their_totals(api_db, shop, paid):
    assert set(run(api_db, shop).totals) == {"units", "revenue", "orders", "avg_ticket"}


# --- other kinds ---------------------------------------------------------------------------------------------

@pytest.fixture
def stock(api_db, market):
    """Own inventory: A1 9 (2 reserved, min 1) + A2 product 0 1 unit (min 5); foreign B1 9; movements in each."""
    from app.models.inventory import Inventory
    from app.models.inventory_movement import InventoryMovement

    api_db.add(Inventory(tenant_id=market.own.tenant.id, variant_id=market.own.variant.id,
                         branch_id=market.branches[1].id, quantity=1, reserved_quantity=0, minimum_stock=5))
    market.foreign.inventory.minimum_stock = 50
    noon = datetime.combine(date.today() - timedelta(days=1), datetime.min.time().replace(hour=12), LA_PAZ)
    for group, branch, qty in ((market.own, 0, 4), (market.own, 1, 3), (market.foreign, 2, 7)):
        api_db.add(InventoryMovement(tenant_id=group.tenant.id, variant_id=group.variant.id,
                                     branch_id=market.branches[branch].id, movement_type="income",
                                     quantity=qty, created_at=noon))
    old = datetime.combine(date.today() - timedelta(days=60), datetime.min.time().replace(hour=12), LA_PAZ)
    api_db.add(InventoryMovement(tenant_id=market.own.tenant.id, variant_id=market.own.variant.id,
                                 branch_id=market.branches[0].id, movement_type="outcome", quantity=1,
                                 created_at=old))
    api_db.commit()
    return market


def kind(api_db, market, name, **spec):
    from app.services.analytics_service import run_query
    spec.setdefault("period", {"preset": "last_n_days", "n": 7})
    return run_query(api_db, market.own.tenant.id, AnalyticsQuery(kind=name, **spec), date.today())


def test_inventory_kind(api_db, stock):
    result = kind(api_db, stock, "inventory", top_n=1, group_by=["customer", "month"], metric="customers")
    assert [c["key"] for c in result.columns] == ["branch", "product", "variant", "quantity", "reserved", "available"]
    assert [c["label"] for c in result.columns] == ["Sucursal", "Producto", "Variante", "Stock", "Reservado",
                                                    "Disponible"]
    assert result.rows == [
        {"branch": "A1", "product": "Product 0 active", "variant": "SKU-0-active", "quantity": 9, "reserved": 2,
         "available": 7},
        {"branch": "A2", "product": "Product 0 active", "variant": "SKU-0-active", "quantity": 1, "reserved": 0,
         "available": 1},
    ]
    assert result.totals == {"items": 2, "units": 10, "available": 8}
    assert result.title == "Inventario por sucursal" and result.chart == "table"
    assert result.period["label"].startswith("Existencias actuales")
    assert result.delta_pct is None and result.previous_totals is None and result.message is None


def test_inventory_kind_honors_several_ids_and_categories(api_db, stock):
    """Several ids skip the legacy single-id SQL filter: only the strict Python filter keeps the third row out."""
    from app.models.branch import Branch
    from app.models.category import Category
    from app.models.inventory import Inventory
    from app.models.product import Product
    from app.models.product_variant import ProductVariant

    own = stock.own.tenant.id
    a3, other = Branch(name="A3", city="City", tenant_id=own), Category(name="Extra", tenant_id=own)
    api_db.add_all([a3, other])
    api_db.flush()
    jacket = Product(name="Chaqueta", tenant_id=own, category_id=other.id)
    api_db.add(jacket)
    api_db.flush()
    jacket_variant = ProductVariant(tenant_id=own, product_id=jacket.id, sku="SKU-CH", price=10)
    api_db.add(jacket_variant)
    api_db.flush()
    api_db.add_all([Inventory(tenant_id=own, variant_id=jacket_variant.id, branch_id=stock.branches[0].id, quantity=4),
                    Inventory(tenant_id=own, variant_id=stock.own.variant.id, branch_id=a3.id, quantity=2)])
    api_db.flush()
    # rows: A1/Product 0, A1/Chaqueta, A2/Product 0, A3/Product 0
    pairs = lambda result: sorted((r["branch"], r["product"]) for r in result.rows)  # noqa: E731
    assert len(kind(api_db, stock, "inventory").rows) == 4
    a1, a2 = stock.branches[0].id, stock.branches[1].id
    assert pairs(kind(api_db, stock, "inventory", branch_ids=[a1, a2])) == [
        ("A1", "Chaqueta"), ("A1", "Product 0 active"), ("A2", "Product 0 active")]
    assert [r["branch"] for r in kind(api_db, stock, "inventory", branch_ids=[a2]).rows] == ["A2"]
    two_products = kind(api_db, stock, "inventory", product_ids=[stock.own.product.id, stock.own.pending.id])
    assert pairs(two_products) == [("A1", "Product 0 active"), ("A2", "Product 0 active"), ("A3", "Product 0 active")]
    assert kind(api_db, stock, "inventory", product_ids=[stock.own.pending.id]).rows == []
    # Category 0 holds Product 0 and the pending product (two ids): Chaqueta (category Extra) must be excluded
    assert {r["product"] for r in kind(api_db, stock, "inventory", category_ids=[stock.own.category.id]).rows} \
        == {"Product 0 active"}
    assert pairs(kind(api_db, stock, "inventory", category_ids=[other.id])) == [("A1", "Chaqueta")]
    assert pairs(kind(api_db, stock, "inventory", branch_ids=[a1, a3.id], category_ids=[stock.own.category.id])) == [
        ("A1", "Product 0 active"), ("A3", "Product 0 active")]
    empty = kind(api_db, stock, "inventory", category_ids=[stock.own.spare_category.id])
    assert empty.rows == [] and empty.message == "No hay existencias para los filtros seleccionados"
    # a foreign branch id (never reached through the routes) still returns nothing foreign
    assert kind(api_db, stock, "inventory", branch_ids=[stock.branches[2].id]).rows == []


def test_critical_stock_kind(api_db, stock):
    result = kind(api_db, stock, "critical_stock")
    assert [c["key"] for c in result.columns] == ["branch", "product", "variant", "available", "minimum"]
    assert result.rows == [{"branch": "A2", "product": "Product 0 active", "variant": "SKU-0-active",
                            "available": 1, "minimum": 5}]
    assert result.totals == {"items": 1} and result.title == "Stock crítico por sucursal"
    none = kind(api_db, stock, "critical_stock", branch_ids=[stock.branches[0].id])
    assert none.rows == [] and none.message == "No hay productos con stock crítico"


def test_movements_kind(api_db, stock):
    result = kind(api_db, stock, "movements")
    assert [c["key"] for c in result.columns] == ["branch", "product", "variant", "movement_type", "quantity",
                                                  "movements"]
    assert result.rows == [
        {"branch": "A1", "product": "Product 0 active", "variant": "SKU-0-active", "movement_type": "Entrada",
         "quantity": 4, "movements": 1},
        {"branch": "A2", "product": "Product 0 active", "variant": "SKU-0-active", "movement_type": "Entrada",
         "quantity": 3, "movements": 1},
    ]
    assert result.totals == {"items": 2, "units": 7} and result.title == "Movimientos de inventario"
    assert result.period["from_date"] == date.today() - timedelta(days=6)
    older = kind(api_db, stock, "movements", period={"preset": "last_n_months", "n": 3})
    assert {r["movement_type"] for r in older.rows} == {"Entrada", "Salida"}
    empty = kind(api_db, stock, "movements", period={"preset": "today"})
    assert empty.rows == [] and empty.message == "No hay movimientos de inventario en el período seleccionado"


@pytest.mark.parametrize("name", ["inventory", "critical_stock", "movements"])
def test_kinds_never_show_the_foreign_company(api_db, stock, name):
    result = kind(api_db, stock, name)
    assert {r["branch"] for r in result.rows} <= {"A1", "A2"}
    assert "Product 1 active" not in str(result.rows)


def test_movement_days_are_la_paz_days(reports_api, api_db, market):
    """21:00 in La Paz is 01:00 UTC next day: last-day evening counts, the evening before the first day does not."""
    from sqlalchemy import text

    from app.models.inventory_movement import InventoryMovement

    # The disposable DB defaults to America/La_Paz, which would hide the bug: run like the VPS (UTC session).
    api_db.execute(text("SET LOCAL TIME ZONE 'UTC'"))
    first, last = date.today() - timedelta(days=5), date.today() - timedelta(days=3)
    for day, movement_type, qty in ((last, "income", 5), (first - timedelta(days=1), "outcome", 7)):
        api_db.add(InventoryMovement(tenant_id=market.own.tenant.id, variant_id=market.own.variant.id,
                                     branch_id=market.branches[0].id, movement_type=movement_type, quantity=qty,
                                     created_at=datetime(day.year, day.month, day.day, 21, tzinfo=LA_PAZ)))
    api_db.commit()
    result = kind(api_db, market, "movements",
                  period={"preset": "custom", "from_date": first.isoformat(), "to_date": last.isoformat()})
    assert [(r["movement_type"], r["quantity"]) for r in result.rows] == [("Entrada", 5)]
    legacy = call(reports_api, market.staff[0, "administrador"], "GET", "/reports/movements",
                  params={"from_date": first.isoformat(), "to_date": last.isoformat()})
    assert [(r["movement_type"], r["quantity"]) for r in legacy["rows"]] == [("income", 5)]


# --- routes and export ---------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["inventory", "critical_stock", "movements"])
def test_manager_is_forced_to_own_branch_for_new_kinds(reports_api, stock, name):
    manager = stock.staff[0, "encargado"]
    data = call(reports_api, manager, "POST", "/reports/analytics",
                json={"kind": name, "period": {"preset": "last_n_days", "n": 7},
                      "branch_ids": [str(stock.branches[1].id)]})
    assert {r["branch"] for r in data["rows"]} <= {"A1"}
    admin = call(reports_api, stock.staff[0, "administrador"], "POST", "/reports/analytics",
                 json={"kind": name, "period": {"preset": "last_n_days", "n": 7}})
    assert "A2" in {r["branch"] for r in admin["rows"]}


@pytest.mark.parametrize("field", ["branch_ids", "product_ids", "category_ids"])
def test_new_kinds_reject_foreign_ids(reports_api, stock, field):
    item = {"branch_ids": stock.branches[2], "product_ids": stock.foreign.product,
            "category_ids": stock.foreign.category}[field]
    result = reports_api.post("/api/reports/analytics", headers=headers(stock.staff[0, "administrador"]),
                              json={"kind": "inventory", "period": {"preset": "today"}, field: [str(item.id)]})
    assert result.status_code == 422, result.text


@pytest.mark.parametrize("name, title", [("inventory", "inventario-por-sucursal"),
                                         ("critical_stock", "stock-critico-por-sucursal"),
                                         ("movements", "movimientos-de-inventario")])
def test_export_of_non_sales_kinds(reports_api, stock, name, title):
    from pypdf import PdfReader
    admin = stock.staff[0, "administrador"]
    body = {"kind": name, "period": {"preset": "last_n_days", "n": 7}}
    xlsx = reports_api.post("/api/reports/analytics/export?format=excel", headers=headers(admin), json=body)
    assert xlsx.status_code == 200, xlsx.text
    assert title in xlsx.headers["content-disposition"]
    ws = load_workbook(BytesIO(xlsx.content)).active
    assert ws["A6"].value == "Sucursal" and ws["A7"].value in ("A1", "A2")
    assert "Subtotal" not in [c.value for c in ws["A"]]
    pdf = reports_api.post("/api/reports/analytics/export?format=pdf", headers=headers(admin), json=body)
    assert pdf.content.startswith(b"%PDF-")
    text = "\n".join(page.extract_text() for page in PdfReader(BytesIO(pdf.content)).pages)
    assert "Sucursal" in text and "Ticket promedio" not in text and "Ingresos" not in text


# --- descriptions --------------------------------------------------------------------------------------------

@pytest.mark.parametrize("spec, expected", [
    ({"kind": "inventory"}, "Inventario por sucursal, existencias actuales"),
    ({"kind": "critical_stock"}, "Stock crítico por sucursal, existencias actuales"),
    ({"kind": "movements", "period": {"preset": "last_week"}}, "Movimientos de inventario, del 02/11/2026 al 08/11/2026"),
    ({"metric": "revenue", "group_by": ["customer"], "top_n": 5},
     "Top 5 clientes que más compran por ingresos, del 13/10/2026 al 11/11/2026"),
    ({"metric": "customers", "group_by": [], "period": {"preset": "last_year"}},
     "Clientes distintos, del 01/01/2025 al 31/12/2025"),
    ({"metric": "revenue", "group_by": ["branch"], "payment_methods": ["cash", "qr"]},
     "Ingresos por sucursal, en efectivo y con QR, del 13/10/2026 al 11/11/2026"),
    ({"metric": "units", "group_by": [], "payment_methods": ["card", "wallet", "cash"],
      "period": {"preset": "this_quarter"}},
     "Unidades vendidas, con tarjeta, con billetera y en efectivo, del 01/10/2026 al 11/11/2026"),
])
def test_describe_new_fields(spec, expected):
    from app.services.natural_report_service import describe_query
    spec.setdefault("period", {"preset": "last_n_days", "n": 30})
    assert describe_query(AnalyticsQuery(**spec), WEDNESDAY) == expected


def test_customers_metric_by_customer_title():
    from app.services.natural_report_service import describe_query
    spec = AnalyticsQuery(metric="customers", group_by=["customer"], period=PeriodSpec(preset="today"))
    assert describe_query(spec, WEDNESDAY) == "Clientes distintos, del 11/11/2026 al 11/11/2026"


def test_export_shows_customers_card_only_when_present():
    from pypdf import PdfReader
    from app.schemas.analytics_schema import AnalyticsResult
    from app.services.report_export_service import analytics_to_excel, analytics_to_pdf

    base = dict(title="Clientes que más compran por ingresos", period={"label": "x"}, chart="bar",
                columns=[{"key": "customer", "label": "Cliente", "type": "text"},
                         {"key": "revenue", "label": "Ingresos (Bs.)", "type": "money"}],
                rows=[{"customer": "Ana", "revenue": 10}])
    sales = {"units": 1, "revenue": 10, "orders": 1, "avg_ticket": 10}
    for totals, shown in ((sales, False), ({**sales, "customers": 7}, True)):
        result = AnalyticsResult(**base, totals=totals)
        text = "\n".join(p.extract_text() for p in PdfReader(BytesIO(analytics_to_pdf(result, "E", "U"))).pages)
        assert ("Clientes distintos" in text) is shown
        ws = load_workbook(BytesIO(analytics_to_excel(result, "E", "U"))).active
        assert ws["A5"].value == ("Clientes distintos: 7" if shown else None)
