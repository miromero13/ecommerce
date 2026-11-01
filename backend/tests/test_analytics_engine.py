"""CU08 analytics engine: one query language over in-store sales and paid online orders.
Own company has branches A1/A2; the foreign company sells in B1 and must never show up."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from itertools import groupby
from operator import itemgetter
from types import SimpleNamespace

import pytest

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_marketplace_transactions import market  # noqa: F401 (shared fixture)

TODAY = date(2026, 11, 10)
LA_PAZ = timezone(timedelta(hours=-4))


def at(day, hour=12, minute=0):
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=LA_PAZ)


@pytest.fixture
def shop(api_db, market):
    from app.models.order import Order
    from app.models.order_item import OrderItem
    from app.models.product import Product
    from app.models.product_variant import ProductVariant
    from app.models.sale import Sale
    from app.models.sale_item import SaleItem

    def product(name, group=market.own):
        item = Product(name=name, tenant_id=group.tenant.id, category_id=group.category.id)
        api_db.add(item)
        api_db.flush()
        variant = ProductVariant(tenant_id=group.tenant.id, product_id=item.id, sku=f"SKU-{name}", price=10)
        api_db.add(variant)
        api_db.flush()
        return variant

    def line(model, variant, qty, total):
        return model(variant_id=variant.id, product_id=variant.product_id, product_name="snapshot",
                     variant_sku=variant.sku, size_id=variant.size_id,
                     color_id=variant.color_id, quantity=qty, unit_price=Decimal(total) / qty, line_total=total)

    def sell(variant, qty, total, when, branch=0, **extra):
        cashier = market.staff[branch, "cajero"]
        api_db.add(Sale(tenant_id=cashier.tenant_id, branch_id=cashier.branch_id, user_id=cashier.id,
                        payment_method="cash", total_amount=total, created_at=when,
                        items=[line(SaleItem, variant, qty, total)], **extra))
        api_db.flush()

    def order(variant, qty, total, when, branch=0, status="paid"):
        api_db.add(Order(tenant_id=market.branches[branch].tenant_id, user_id=market.customer.id,
                         pickup_branch_id=market.branches[branch].id, status=status,
                         payment_method="stripe", payment_status="paid" if status == "paid" else "pending",
                         total_amount=total, created_at=when, items=[line(OrderItem, variant, qty, total)]))
        api_db.flush()

    return SimpleNamespace(product=product, sell=sell, order=order, tenant=market.own.tenant,
                           variant=market.own.variant, own=market.own, foreign=market.foreign)


def run(api_db, shop, **spec):
    from app.schemas.analytics_schema import AnalyticsQuery
    from app.services.analytics_service import run_query

    spec.setdefault("period", {"preset": "today"})
    return run_query(api_db, shop.tenant.id, AnalyticsQuery(**spec), TODAY)


def test_engineer_query_top_10_per_branch_last_3_months(api_db, shop):
    from app.schemas.analytics_schema import AnalyticsQuery, PeriodSpec
    from app.services.analytics_service import run_query

    for i in range(1, 13):
        variant = shop.product(f"Prenda {i:02d}")
        shop.sell(variant, i, 10 * i, at(TODAY - timedelta(days=30)), branch=0)
        shop.sell(variant, 13 - i, 10 * (13 - i), at(TODAY - timedelta(days=60)), branch=1)
    # 2026-08-10 23:30 in La Paz is already 08-11 in UTC, but it is still outside the period.
    shop.sell(shop.product("Fuera de periodo"), 100, 1000, at(date(2026, 8, 10), 23, 30))
    q = AnalyticsQuery(metric="units", group_by=["branch", "product"], top_n=10,
                       period=PeriodSpec(preset="last_n_months", n=3))
    result = run_query(api_db, shop.tenant.id, q, TODAY)
    by_branch = {branch: list(rows) for branch, rows in groupby(result.rows, key=itemgetter("branch"))}
    assert list(by_branch) == ["A1", "A2"]
    assert all(len(rows) == 10 for rows in by_branch.values())
    assert [c["key"] for c in result.columns] == ["branch", "product", "units"]
    assert [c["label"] for c in result.columns] == ["Sucursal", "Producto", "Unidades"]
    assert result.rows[0] == {"branch": "A1", "product": "Prenda 12", "units": 12}
    assert result.rows[0]["units"] >= result.rows[1]["units"]
    assert [r["units"] for r in by_branch["A2"]] == list(range(12, 2, -1))
    assert "Fuera de periodo" not in {r["product"] for r in result.rows}
    assert result.title == "Top 10 productos por unidades vendidas, agrupado por sucursal"
    assert result.period["from_date"] == date(2026, 8, 11) and result.chart == "bar"
    assert result.message is None


def test_online_and_store_sales_are_both_counted(api_db, shop):
    # 22:30 in La Paz is already tomorrow in UTC: still "today" for the company.
    shop.sell(shop.variant, 2, 50, at(TODAY, 22, 30))
    shop.order(shop.variant, 1, 25, at(TODAY, 22, 30))
    result = run(api_db, shop, group_by=["channel"])
    assert result.rows == [{"channel": "En línea", "units": 1}, {"channel": "Tienda", "units": 2}]
    assert result.chart == "donut"


def test_revenue_orders_and_avg_ticket(api_db, shop):
    shop.sell(shop.variant, 1, 50, at(TODAY))
    shop.sell(shop.variant, 3, 150, at(TODAY))
    result = run(api_db, shop, metric="revenue", group_by=["day"])
    assert result.totals == {"revenue": Decimal("200.00"), "orders": 2,
                             "avg_ticket": Decimal("100.00"), "units": 4}
    assert result.rows == [{"day": "2026-11-10", "revenue": Decimal("200.00")}]
    assert result.columns[-1] == {"key": "revenue", "label": "Ingresos (Bs.)", "type": "money"}
    assert result.chart == "line"


def test_compare_previous_period_delta(api_db, shop):
    shop.sell(shop.variant, 4, 100, at(date(2026, 10, 25)))
    shop.sell(shop.variant, 6, 150, at(date(2026, 11, 5)))
    result = run(api_db, shop, metric="revenue", group_by=["month"], compare_previous=True,
                 period={"preset": "custom", "from_date": "2026-11-01", "to_date": "2026-11-10"})
    assert result.previous_totals["revenue"] == Decimal("100.00")
    assert result.delta_pct["revenue"] == 50.0
    assert result.delta_pct["units"] == 50.0
    assert result.rows == [{"month": "2026-11", "revenue": Decimal("150.00")}]


def test_empty_period_returns_empty_rows(api_db, shop):
    shop.sell(shop.variant, 1, 25, at(TODAY - timedelta(days=1)))
    result = run(api_db, shop, compare_previous=True)
    assert result.rows == [] and result.message == "No hay ventas en el período seleccionado"
    assert result.totals == {"units": 0, "revenue": Decimal("0.00"), "orders": 0, "avg_ticket": Decimal("0.00")}
    assert result.previous_totals["units"] == 1 and result.delta_pct["units"] == -100.0


def test_top_n_ties_are_deterministic(api_db, shop):
    for name in ("Blusa C", "Blusa A", "Blusa B"):
        shop.sell(shop.product(name), 5, 50, at(TODAY))
    result = run(api_db, shop, group_by=["product"], top_n=2)
    assert [r["product"] for r in result.rows] == ["Blusa A", "Blusa B"]
    assert result.title == "Top 2 productos por unidades vendidas"


def test_other_company_sales_never_appear(api_db, shop):
    shop.sell(shop.variant, 1, 25, at(TODAY))
    foreign = shop.foreign.variant
    shop.sell(foreign, 9, 225, at(TODAY), branch=2)
    shop.order(foreign, 9, 225, at(TODAY), branch=2)
    result = run(api_db, shop, group_by=["product"])
    assert {r["product"] for r in result.rows} == {shop.own.product.name}
    assert shop.foreign.product.name not in {r["product"] for r in result.rows}
    assert result.totals["units"] == 1


@pytest.mark.parametrize("dim, label", [
    ("variant", "SKU-0-active"), ("category", "Category 0"), ("branch", "A1"), ("size", "M"),
    ("color", "Blue"), ("payment_method", "Efectivo"), ("week", "Semana del 2026-11-09"),
])
def test_every_dimension_has_a_readable_label(api_db, shop, dim, label):
    shop.sell(shop.variant, 1, 25, at(TODAY))
    assert run(api_db, shop, group_by=[dim]).rows == [{dim: label, "units": 1}]


def test_cancelled_and_unpaid_sales_are_excluded(api_db, shop):
    shop.sell(shop.variant, 1, 25, at(TODAY))
    shop.sell(shop.variant, 10, 250, at(TODAY), status="cancelled")
    shop.sell(shop.variant, 20, 500, at(TODAY), payment_status="pending")
    shop.order(shop.variant, 30, 750, at(TODAY), status="pending")
    shop.order(shop.variant, 40, 1000, at(TODAY), status="cancelled")
    result = run(api_db, shop, group_by=["channel"])
    assert result.rows == [{"channel": "Tienda", "units": 1}]
    assert result.totals["units"] == 1 and result.totals["orders"] == 1
