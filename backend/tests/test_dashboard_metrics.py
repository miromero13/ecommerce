"""CU13 dashboard: comparison vs previous period, channel split, top categories and low stock."""
from datetime import date
from uuid import UUID

from test_analytics_engine import at, shop  # noqa: F401 (shared fixtures)
from test_catalog_tenant_isolation import catalog  # noqa: F401
from test_marketplace_transactions import market  # noqa: F401


def dash(api_db, shop, **kw):
    from app.schemas.dashboard_schema import DashboardQuery
    from app.services.dashboard_service import get_dashboard

    return get_dashboard(api_db, DashboardQuery(**kw), shop.tenant.id)


RANGE = {"from_date": date(2026, 11, 1), "to_date": date(2026, 11, 10)}  # previous: Oct 22-31


def test_dashboard_comparison_deltas(api_db, shop):
    shop.sell(shop.variant, 4, 100, at(date(2026, 10, 25)))
    shop.sell(shop.variant, 6, 150, at(date(2026, 11, 5)))
    shop.sell(shop.variant, 1, 25, at(date(2026, 11, 6)))
    data = dash(api_db, shop, **RANGE)
    # 2 orders / 7 units / 175 vs 1 order / 4 units / 100 (avg ticket 87.5 vs 100)
    assert data.comparison.sales_delta_pct == 75.0
    assert data.comparison.orders_delta_pct == 100.0
    assert data.comparison.units_delta_pct == 75.0
    assert data.comparison.avg_ticket_delta_pct == -12.5


def test_dashboard_comparison_is_none_without_data_or_dates(api_db, shop):
    shop.sell(shop.variant, 1, 25, at(date(2026, 11, 5)))
    no_previous = dash(api_db, shop, **RANGE)
    assert no_previous.comparison.sales_delta_pct is None
    unbounded = dash(api_db, shop)
    assert unbounded.comparison.sales_delta_pct is None
    empty = dash(api_db, shop, from_date=date(2025, 1, 1), to_date=date(2025, 1, 10))
    assert empty.channel_split == [] and empty.top_categories == []


def test_dashboard_channel_split_includes_online(api_db, shop):
    shop.sell(shop.variant, 2, 50, at(date(2026, 11, 5)))
    shop.order(shop.variant, 1, 25, at(date(2026, 11, 5)))
    shop.order(shop.variant, 1, 25, at(date(2026, 11, 6)))
    shop.sell(shop.foreign.variant, 9, 225, at(date(2026, 11, 5)), branch=2)
    data = dash(api_db, shop, **RANGE)
    split = {c.channel_label: (float(c.sales), c.orders) for c in data.channel_split}
    assert split == {"Tienda": (50.0, 1), "En línea": (50.0, 2)}
    assert [(c.category_name, c.units, float(c.sales)) for c in data.top_categories] == [("Category 0", 4, 100.0)]
    assert dash(api_db, shop, **RANGE, branch_id=shop.own.inventory.branch_id).top_categories[0].units == 4


def test_dashboard_low_stock_list_is_tenant_scoped(api_db, shop):
    shop.own.inventory.minimum_stock = 7  # available 9 - 2 = 7 <= 7
    shop.foreign.inventory.reserved_quantity = 9  # foreign available 0 <= 1: must not leak
    api_db.flush()
    data = dash(api_db, shop)
    assert [(r.product_name, r.sku, r.available, r.minimum) for r in data.low_stock] == [
        (shop.own.product.name, shop.own.variant.sku, 7, 7)]
    assert data.low_stock[0].branch_name == "A1"
    other_branch = dash(api_db, shop, branch_id=UUID(int=1))
    assert other_branch.low_stock == []


def test_dashboard_summary_low_stock_count_matches_list_and_branch_filter(api_db, shop):
    from app.models.branch import Branch
    from app.models.inventory import Inventory

    a1 = shop.own.inventory.branch_id
    a2 = api_db.query(Branch).filter(Branch.tenant_id == shop.tenant.id, Branch.name == "A2").one().id
    shop.own.inventory.minimum_stock = 7  # new criterion: low (7 <= 7); old one (9 <= 2): not low
    other = shop.product("Otra")
    api_db.add(Inventory(tenant_id=shop.tenant.id, variant_id=other.id, branch_id=a2,
                         quantity=3, reserved_quantity=0, minimum_stock=3))
    api_db.flush()
    data = dash(api_db, shop)
    assert data.summary.low_stock_items == len(data.low_stock) == 2
    assert [r.available for r in data.low_stock] == [3, 7]
    only_a2 = dash(api_db, shop, branch_id=a2)
    assert only_a2.summary.low_stock_items == 1
    assert [(r.branch_name, r.available) for r in only_a2.low_stock] == [("A2", 3)]
    shop.order(other, 1, 10, at(date(2026, 11, 5)), branch=1)
    shop.sell(shop.variant, 2, 50, at(date(2026, 11, 5)), branch=0)
    split = {c.channel_label: c.orders for c in dash(api_db, shop, **RANGE, branch_id=a2).channel_split}
    assert split == {"En línea": 1}


def test_dashboard_year_one_range_does_not_overflow(api_db, shop):
    data = dash(api_db, shop, from_date=date(1, 1, 1), to_date=date(1, 1, 5))
    assert data.comparison.sales_delta_pct is None
    assert data.comparison.orders_delta_pct is None
    assert data.comparison.units_delta_pct is None
    assert data.comparison.avg_ticket_delta_pct is None
