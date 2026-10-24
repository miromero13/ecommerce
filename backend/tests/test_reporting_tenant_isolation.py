"""CU1: missing BI/coupon scope predicates must leak these distinct real rows."""
import csv
from datetime import date
from decimal import Decimal
from io import StringIO

import pytest
from sqlalchemy import text

from test_catalog_tenant_isolation import catalog
from test_employee_authorization import headers


@pytest.fixture(autouse=True)
def reporting_routes(api):
    from app.routes import dashboard_routes, promotion_routes, report_routes
    for module in (dashboard_routes, promotion_routes, report_routes):
        api.app.include_router(module.router, prefix="/api")


@pytest.fixture
def business(api_db, catalog):
    from app.models.inventory_movement import InventoryMovement
    from app.models.order import Order
    from app.models.order_item import OrderItem
    from app.models.promotion_code import PromotionCode
    from app.models.reservation import Reservation
    from app.models.sale import Sale
    from app.models.sale_item import SaleItem
    for group, branch, quantity in ((catalog.own, catalog.branches[0], 2),
                                    (catalog.own, catalog.branches[1], 1),
                                    (catalog.foreign, catalog.branches[2], 8)):
        sale = Sale(tenant_id=group.tenant.id, branch_id=branch.id, user_id=catalog.user.id,
                    payment_method="cash", subtotal=quantity * 25, total_amount=quantity * 25)
        api_db.add(sale)
        api_db.flush()
        api_db.add(SaleItem(sale_id=sale.id, variant_id=group.variant.id, quantity=quantity,
                           unit_price=25, line_total=quantity * 25, product_id=group.product.id,
                           product_name=group.product.name, variant_sku=group.variant.sku))
        api_db.add(InventoryMovement(tenant_id=group.tenant.id, branch_id=branch.id,
                                    variant_id=group.variant.id, movement_type="income", quantity=quantity))
    for group, branch, quantity in ((catalog.own, catalog.branches[0], 1),
                                    (catalog.foreign, catalog.branches[2], 4)):
        order = Order(tenant_id=group.tenant.id, pickup_branch_id=branch.id, user_id=catalog.user.id,
                      payment_method="cash", status="paid", payment_status="paid",
                      subtotal=quantity * 25, total_amount=quantity * 25)
        api_db.add(order)
        api_db.flush()
        api_db.add(OrderItem(order_id=order.id, variant_id=group.variant.id, quantity=quantity,
                            unit_price=25, line_total=quantity * 25, product_id=group.product.id,
                            product_name=group.product.name, variant_sku=group.variant.sku))
        api_db.add(Reservation(tenant_id=group.tenant.id, branch_id=branch.id, user_id=catalog.user.id,
                               visit_date=date.today(), expires_at=date.today(), total_amount=25))
        for suffix, branch_id in (("GLOBAL", None), ("BRANCH", branch.id)):
            api_db.add(PromotionCode(tenant_id=group.tenant.id, code=group.tenant.slug.upper() + suffix,
                                     discount_type="fixed", discount_value=5, branch_id=branch_id,
                                     created_by=catalog.user.id))
    # A foreign low-stock alert must not appear in the own-company dashboard.
    catalog.foreign.inventory.reserved_quantity = 9
    api_db.commit()
    return catalog


def get(api, path, user, **params):
    result = api.get("/api" + path, headers=headers(user), params=params)
    assert result.status_code == 200, result.text
    return result.json()["data"]


def snapshot(db):
    tables = ("tenants", "users", "branches", "products", "product_variants", "inventory",
              "inventory_movements", "sales", "sale_items", "orders", "order_items", "reservations",
              "promotion_codes", "promotion_code_usages", "saas_plans", "tenant_subscriptions")
    return {table: db.execute(text(f"SELECT row_to_json(t)::text FROM {table} t ORDER BY id")).all()
            for table in tables}


@pytest.mark.parametrize("family", ["sales", "inventory", "movements"])
@pytest.mark.parametrize("suffix", ["", "/export"])
@pytest.mark.parametrize("field", ["branch_id", "product_id", "variant_id"])
def test_missing_report_filter_preserves_success_contract(api, api_db, business, family, suffix, field):
    from uuid import uuid4

    before = snapshot(api_db)
    result = api.get(f"/api/reports/{family}{suffix}", headers=headers(business.user),
                     params={field: str(uuid4())})
    assert result.status_code == 200, result.text
    if suffix:
        assert list(csv.DictReader(StringIO(result.text))) == []
    else:
        assert result.json()["data"]["rows"] == []
    assert snapshot(api_db) == before


def test_missing_dashboard_branch_preserves_success_contract(api, api_db, business):
    from uuid import uuid4

    before = snapshot(api_db)
    result = api.get("/api/dashboard", headers=headers(business.user),
                     params={"branch_id": str(uuid4())})
    assert result.status_code == 200, result.text
    data = result.json()["data"]
    assert data["branch_kpis"] == []
    assert data["sales_series"] == []
    assert data["summary"]["total_orders"] == 0
    assert snapshot(api_db) == before


@pytest.mark.parametrize("family", ["sales", "inventory", "movements"])
@pytest.mark.parametrize("export", [False, True])
def test_conventional_reports_and_csv_contain_only_company_rows(api, business, family, export):
    c = business
    path = f"/reports/{family}" + ("/export" if export else "")
    result = api.get("/api" + path, headers=headers(c.user))
    assert result.status_code == 200, result.text
    if export:
        assert result.headers["content-type"].startswith("text/csv")
        assert result.headers["content-disposition"] == f'attachment; filename="{family}-report.csv"'
        rows = list(csv.DictReader(StringIO(result.text)))
    else:
        report = result.json()["data"]
        rows = report["rows"]
        if family == "inventory":
            assert report["summary"] == {"total_lines": 1, "total_stock": 9, "total_reserved": 2, "total_available": 7}
        elif family == "movements":
            assert report["summary"] == {"total_lines": 2, "total_units_moved": 3}
        else:
            assert report["summary"]["total_orders"] == 3
            assert report["summary"]["total_units"] == 4
            assert Decimal(report["summary"]["total_sales"]) == Decimal("100.00")
    assert {row["product_id"] for row in rows} == {str(c.own.product.id)}
    assert {row["branch_id"] for row in rows} <= {str(branch.id) for branch in c.branches[:2]}
    if family == "inventory":
        assert len(rows) == 1
        assert tuple(int(rows[0][key]) for key in ("quantity", "reserved_quantity", "available_quantity")) == (9, 2, 7)
    elif family == "movements":
        assert sorted(int(row["quantity"]) for row in rows) == [1, 2]
    else:
        assert sorted((row["type"], int(row["quantity_sold"])) for row in rows) == [
            ("venta presencial", 1), ("venta presencial", 2), ("venta virtual", 1)]
        assert sum(Decimal(row["gross_sales"]) for row in rows) == Decimal("100.00")


@pytest.mark.parametrize("family", ["sales", "inventory", "movements"])
@pytest.mark.parametrize("export", [False, True])
@pytest.mark.parametrize("role", ["administrador", "encargado"])
@pytest.mark.parametrize("field,attribute", [
    ("branch_id", None), ("product_id", "product"), ("variant_id", "variant"),
])
def test_foreign_filters_never_return_foreign_company_data(api, api_db, business, family, export, role, field, attribute):
    from app.schemas.enums import RolEnum
    c = business
    c.user.rol, c.user.branch_id = RolEnum(role), c.branches[0].id
    api_db.commit()
    item = c.branches[2] if attribute is None else getattr(c.foreign, attribute)
    before = snapshot(api_db)
    path = f"/api/reports/{family}" + ("/export" if export else "")
    result = api.get(path, headers=headers(c.user), params={field: str(item.id)})
    assert result.status_code == 200, result.text
    rows = list(csv.DictReader(StringIO(result.text))) if export else result.json()["data"]["rows"]
    if role == "encargado" and field == "branch_id":
        # Existing behavior: a query parameter cannot replace the assigned branch.
        assert {row["branch_id"] for row in rows} == {str(c.branches[0].id)}
        key = {"sales": "quantity_sold", "inventory": "available_quantity", "movements": "quantity"}[family]
        assert sum(int(row[key]) for row in rows) == {"sales": 3, "inventory": 7, "movements": 2}[family]
    else:
        assert rows == []
    assert all(row["branch_id"] != str(c.branches[2].id) for row in rows)
    assert all(row["product_id"] != str(c.foreign.product.id) for row in rows)
    assert snapshot(api_db) == before


@pytest.mark.parametrize("family,expected", [("sales", 3), ("inventory", 7), ("movements", 2)])
def test_manager_report_branch_cannot_be_widened_by_own_company_filter(api, api_db, business, family, expected):
    from app.schemas.enums import RolEnum
    c = business
    c.user.rol, c.user.branch_id = RolEnum.encargado, c.branches[0].id
    api_db.commit()
    for suffix in ("", "/export"):
        result = api.get(f"/api/reports/{family}{suffix}", headers=headers(c.user),
                         params={"branch_id": str(c.branches[1].id)})
        assert result.status_code == 200, result.text
        rows = list(csv.DictReader(StringIO(result.text))) if suffix else result.json()["data"]["rows"]
        assert {row["branch_id"] for row in rows} == {str(c.branches[0].id)}
        key = {"sales": "quantity_sold", "inventory": "available_quantity", "movements": "quantity"}[family]
        assert sum(int(row[key]) for row in rows) == expected


def test_dashboard_scopes_all_aggregate_and_catalog_sections(api, business):
    c = business
    dashboard = get(api, "/dashboard", c.user)
    summary = dashboard["summary"]
    assert Decimal(summary["total_sales"]) == Decimal("75.00")
    assert (summary["total_orders"], summary["total_units_sold"], summary["total_stock"],
            summary["total_available_stock"], summary["total_reservations"], summary["pending_reservations"]) == (2, 3, 9, 7, 1, 1)
    assert {row["branch_id"] for row in dashboard["branch_kpis"]} == {str(branch.id) for branch in c.branches[:2]}
    assert {row["product_id"] for row in dashboard["top_products"]} == {str(c.own.product.id), str(c.own.pending.id)}
    assert sum(Decimal(row["sales"]) for row in dashboard["sales_series"]) == Decimal("75.00")
    assert sum(row["income"] for row in dashboard["movement_series"]) == 3
    assert sum(row["total_stock"] for row in dashboard["branch_kpis"]) == 9
    assert sum(row["total_available_stock"] for row in dashboard["top_products"]) == 7
    assert sum(Decimal(row["total_sales"]) for row in dashboard["top_products"]) == Decimal("75.00")
    assert {row["branch_id"] for row in dashboard["movement_by_branch"]} == {str(branch.id) for branch in c.branches[:2]}
    assert dashboard["low_stock"] == []
    own_branch = get(api, "/dashboard", c.user, branch_id=str(c.branches[0].id))
    assert Decimal(own_branch["summary"]["total_sales"]) == Decimal("50.00")
    assert own_branch["summary"]["total_units_sold"] == 2


def test_dashboard_foreign_branch_preserves_empty_success_without_foreign_data(api, api_db, business):
    before = snapshot(api_db)
    branch_id = business.branches[2].id
    result = api.get("/api/dashboard", headers=headers(business.user), params={"branch_id": str(branch_id)})
    assert result.status_code == 200, result.text
    data = result.json()["data"]
    assert data["branch_kpis"] == []
    assert data["sales_series"] == []
    assert data["summary"]["total_orders"] == 0
    assert Decimal(data["summary"]["total_sales"]) == 0
    assert all(row["product_id"] != str(business.foreign.product.id) for row in data["top_products"])
    assert snapshot(api_db) == before


def test_promotion_lists_and_creation_are_company_scoped(api, api_db, business):
    c = business
    assert {row["code"] for row in get(api, "/promotions", c.user)} == {"ALPHAGLOBAL", "ALPHABRANCH"}
    result = api.post("/api/promotions", headers=headers(c.user), json={
        "code": "new-alpha", "discount_type": "fixed", "discount_value": "5.00"})
    assert result.status_code == 201, result.text
    assert result.json()["message"] == "Código promocional creado"
    assert result.json()["data"]["branch_id"] is None
    assert result.json()["data"]["created_by"] == str(c.user.id)
    assert {row["code"] for row in get(api, "/promotions", c.user)} == {"ALPHAGLOBAL", "ALPHABRANCH", "NEW-ALPHA"}
    c.user.tenant_id = c.foreign.tenant.id
    api_db.commit()
    assert {row["code"] for row in get(api, "/promotions", c.user)} == {"BETAGLOBAL", "BETABRANCH"}


@pytest.mark.parametrize("role,branch_index,code,message", [
    ("administrador", 2, 400, "El administrador solo puede crear códigos globales"),
    ("encargado", 2, 403, "El código debe pertenecer a la sucursal del encargado"),
    ("encargado", 1, 403, "El código debe pertenecer a la sucursal del encargado"),
])
def test_coupon_branch_rules_reject_without_side_effects(api, api_db, business, role, branch_index, code, message):
    from app.schemas.enums import RolEnum
    c = business
    c.user.rol, c.user.branch_id = RolEnum(role), c.branches[0].id
    api_db.commit()
    before = snapshot(api_db)
    result = api.post("/api/promotions", headers=headers(c.user), json={
        "code": "invalid-branch", "discount_type": "fixed", "discount_value": 5,
        "branch_id": str(c.branches[branch_index].id)})
    assert result.status_code == code, result.text
    assert result.json() == {"statusCode": code, "message": message, "error": "HTTPException"}
    assert snapshot(api_db) == before


def test_manager_preserves_branch_coupon_listing_and_creation(api, api_db, business):
    from app.schemas.enums import RolEnum
    c = business
    c.user.rol, c.user.branch_id = RolEnum.encargado, c.branches[0].id
    api_db.commit()
    assert [row["code"] for row in get(api, "/promotions", c.user)] == ["ALPHABRANCH"]
    result = api.post("/api/promotions", headers=headers(c.user), json={
        "code": "branch-new", "discount_type": "percentage", "discount_value": 10,
        "branch_id": str(c.branches[0].id)})
    assert result.status_code == 201, result.text
    assert result.json()["message"] == "Código promocional creado"
    assert {row["code"] for row in get(api, "/promotions", c.user)} == {"ALPHABRANCH", "BRANCH-NEW"}


@pytest.fixture
def interpreter(monkeypatch, api_db, business):
    from app.core.config import settings
    from app.models.subscription_plan import SubscriptionPlan
    from app.schemas.report_schema import NaturalReportInterpretation
    from app.services import natural_report_service
    from app.services.subscription_service import create_or_update_tenant_subscription
    plan = SubscriptionPlan(id="cu1_ai", name="AI fixture", slug="cu1-ai", features=["ai_text_reports"])
    api_db.add(plan)
    api_db.flush()
    create_or_update_tenant_subscription(api_db, business.own.tenant.id, plan.id)
    api_db.commit()
    monkeypatch.setattr(settings, "gemini_api_key", "test-boundary-only")
    observed = []
    interpretation = {"report_type": "inventory", "format": "csv", "interpretation": "Inventario propio",
                      "columns": ["product_name", "quantity", "reserved_quantity", "available_quantity"]}

    def interpret(prompt):
        observed.append(prompt)
        return NaturalReportInterpretation(**interpretation)

    monkeypatch.setattr(natural_report_service, "_interpret_sync", interpret)
    return observed, interpretation


def test_natural_report_scopes_prompt_catalog_and_executed_result(api, business, interpreter):
    prompts, _ = interpreter
    c = business
    result = api.post("/api/reports/query", headers=headers(c.user), json={"query": "Inventario en CSV"})
    assert result.status_code == 200, result.text
    assert result.json()["message"] == "Reporte interpretado exitosamente"
    report = result.json()["data"]["report"]
    assert report["summary"] == {"total_lines": 1, "total_stock": 9, "total_reserved": 2, "total_available": 7}
    assert [row["product_id"] for row in report["rows"]] == [str(c.own.product.id)]
    assert len(prompts) == 1
    assert str(c.own.product.id) in prompts[0]
    assert str(c.branches[0].id) in prompts[0]
    for item in (c.foreign.product, c.foreign.pending, c.branches[2]):
        assert str(item.id) not in prompts[0]
        assert item.name not in prompts[0]


@pytest.mark.parametrize("field,attribute,message", [
    ("branch_id", None, "La sucursal interpretada no existe en el catálogo"),
    ("product_id", "product", "El producto interpretado no existe en el catálogo"),
    ("variant_id", "variant", "La variante interpretada no existe en el catálogo"),
])
def test_natural_report_rejects_foreign_interpreter_ids_before_results(api, api_db, business, interpreter, field, attribute, message):
    _, interpretation = interpreter
    item = business.branches[2] if attribute is None else getattr(business.foreign, attribute)
    interpretation[field] = item.id
    before = snapshot(api_db)
    result = api.post("/api/reports/query", headers=headers(business.user), json={"query": "Inventario"})
    assert result.status_code == 422, result.text
    assert result.json() == {"statusCode": 422, "message": message, "error": message}
    assert snapshot(api_db) == before
