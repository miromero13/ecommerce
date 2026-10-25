"""CU2 plans and subscriptions on the disposable PostgreSQL schema.

Real routes, signed tokens and SQL; only the welcome e-mail and the external
garment image fetch are replaced. Every test rolls back (see conftest).
"""
import pytest
from sqlalchemy import text

from conftest import subscribe
from test_catalog_tenant_isolation import catalog, product_payload  # noqa: F401 (shared fixture)
from test_employee_authorization import headers

NO_PLAN = "Tu empresa no tiene una suscripción activa. Renová o elegí un plan para continuar."


@pytest.fixture
def saas_api(api, monkeypatch):
    from app.routes import auth, garment_routes, report_routes, subscription_routes
    from app.services import email_service as email_module

    sent = []

    async def capture(**kwargs):
        sent.append(kwargs)

    monkeypatch.setattr(email_module.email_service, "send_welcome_credentials_email", capture)
    for module in (auth, garment_routes, report_routes, subscription_routes):
        api.app.include_router(module.router, prefix="/api")
    api.sent = sent
    return api


def call(api, method, path, user=None, code=200, **kwargs):
    result = api.request(method, "/api" + path, headers=headers(user) if user else {}, **kwargs)
    assert result.status_code == code, result.text
    return result.json()


def plan_of(db, tenant, plan_id, days=30):
    """Replace the fixture's Enterprise period with the plan under test."""
    from app.models.subscription_plan import SubscriptionPlan

    db.execute(text("UPDATE tenant_subscriptions SET status = 'canceled' WHERE tenant_id = :id"),
               {"id": tenant.id})
    subscribe(db, tenant, db.get(SubscriptionPlan, plan_id), days=days)
    db.commit()


def subscriptions(db, tenant):
    return db.execute(text(
        "SELECT plan_id, status FROM tenant_subscriptions WHERE tenant_id = :id ORDER BY created_at"
    ), {"id": tenant.id}).all()


def count(db, table, tenant):
    return db.execute(text(f"SELECT count(*) FROM {table} WHERE tenant_id = :id"),
                      {"id": tenant.id}).scalar_one()


def make_user(db, rol, tenant=None, branch=None, email=None):
    from app.models.user import User
    from app.schemas.enums import GenderEnum

    user = User(name=rol.value, email=email or f"{rol.value}@example.com", hashed_password="unused",
                gender=GenderEnum.femenino, rol=rol, tenant_id=tenant.id if tenant else None,
                branch_id=branch.id if branch else None, is_active=True)
    db.add(user)
    db.commit()
    return user


def test_public_plans_list_three_tiers_by_price(saas_api, catalog):
    plans = call(saas_api, "GET", "/saas/plans")["data"]
    assert [plan["id"] for plan in plans] == ["plan_basic", "plan_pro", "plan_enterprise"]
    by_id = {plan["id"]: plan for plan in plans}
    assert "chatbot" not in by_id["plan_basic"]["features"]
    assert {"chatbot", "virtual_try_on_2d", "ai_text_reports"} <= set(by_id["plan_pro"]["features"])
    assert (by_id["plan_basic"]["max_branches"], by_id["plan_basic"]["max_garments"]) == (2, 500)


def test_onboarding_creates_company_admin_and_plan_and_credentials_work(saas_api, catalog):
    body = call(saas_api, "POST", "/saas/subscriptions/purchase-simulated", code=201, json={
        "company_name": "Nueva Marca", "admin_name": "Ana", "admin_email": "ana@nueva.com",
        "plan_id": "plan_basic", "billing_cycle": "monthly",
    })
    assert body["data"]["plan_name"] == "Básico"
    [mail] = saas_api.sent
    assert mail["to_email"] == "ana@nueva.com"
    login = call(saas_api, "POST", "/auth/login", json={"email": "ana@nueva.com", "password": mail["password"]})
    token = {"Authorization": "Bearer " + login["data"]["access_token"]}
    current = saas_api.get("/api/saas/subscriptions/current", headers=token).json()["data"]
    assert current["has_active_subscription"] is True and current["plan"]["id"] == "plan_basic"
    assert current["usage"] == {"branches_count": 0, "branches_max": 2, "garments_count": 0, "garments_max": 500}


def test_superadmin_creates_company_with_cash_plan(saas_api, api_db, catalog):
    from app.schemas.enums import RolEnum

    superadmin = make_user(api_db, RolEnum.superadministrador)
    body = call(saas_api, "POST", "/saas/tenants/with-subscription", superadmin, 201, json={
        "name": "Marca Efectivo", "contact_email": "admin@efectivo.com", "admin_name": "Luis",
        "plan_id": "plan_pro", "billing_cycle": "yearly", "payment_method": "cash",
    })
    current = call(saas_api, "GET", "/saas/subscriptions/current", superadmin,
                   params={"tenant_id": body["data"]["tenant_id"]})["data"]
    assert current["plan"]["id"] == "plan_pro"
    assert (current["subscription"]["payment_method"], current["subscription"]["billing_cycle"]) == ("cash", "yearly")


def test_branch_quota_blocks_creation_at_plan_limit(saas_api, api_db, catalog):
    own = catalog.own.tenant
    plan_of(api_db, own, "plan_basic")  # own company already has 2 branches
    body = call(saas_api, "POST", "/branches/", catalog.user, 403, json={"name": "A3", "city": "La Paz"})
    assert body["message"] == "Límite de sucursales alcanzado para el plan actual. Actualizá tu suscripción."
    assert count(api_db, "branches", own) == 2


def test_garment_quota_blocks_product_creation_at_plan_limit(saas_api, api_db, catalog):
    own = catalog.own.tenant
    plan_of(api_db, own, "plan_basic")
    api_db.execute(text("UPDATE saas_plans SET max_garments = 2 WHERE id = 'plan_basic'"))
    api_db.commit()
    body = call(saas_api, "POST", "/catalog/products", catalog.user, 403, json=product_payload(catalog))
    assert body["message"] == "Límite de prendas alcanzado para el plan actual. Actualizá tu suscripción."
    assert count(api_db, "products", own) == 2


def test_expired_subscription_stops_limits_and_features(saas_api, api_db, catalog):
    own = catalog.own.tenant
    plan_of(api_db, own, "plan_pro", days=-1)
    current = call(saas_api, "GET", "/saas/subscriptions/current", catalog.user)["data"]
    assert current["has_active_subscription"] is False
    for path, payload in (("/branches/", {"name": "A3", "city": "La Paz"}),
                          ("/catalog/products", product_payload(catalog))):
        assert call(saas_api, "POST", path, catalog.user, 403, json=payload)["message"] == NO_PLAN
    report = call(saas_api, "POST", "/reports/query", catalog.user, 403, json={"query": "ventas de hoy"})
    assert "no incluye reportes con Inteligencia Artificial" in report["message"]
    product = call(saas_api, "GET", f"/catalog/products/{catalog.own.product.id}")["data"]
    assert product["try_on_enabled"] is False


def test_admin_upgrades_plan_and_gets_new_limits(saas_api, api_db, catalog):
    own = catalog.own.tenant
    plan_of(api_db, own, "plan_basic")
    body = call(saas_api, "POST", "/saas/subscriptions/change-plan", catalog.user,
                json={"plan_id": "plan_pro", "billing_cycle": "monthly"})
    assert body["message"] == "Plan actualizado con éxito. Tu empresa ahora tiene el plan Profesional."
    assert body["data"]["plan"]["id"] == "plan_pro" and body["data"]["usage"]["branches_max"] == 5
    statuses = [tuple(row) for row in subscriptions(api_db, own)]
    assert statuses.count(("plan_pro", "active")) == 1
    assert [row for row in statuses if row[1] == "active"] == [("plan_pro", "active")]
    call(saas_api, "POST", "/branches/", catalog.user, 201, json={"name": "A3", "city": "La Paz"})


def test_expired_company_can_renew_same_plan(saas_api, api_db, catalog):
    own = catalog.own.tenant
    plan_of(api_db, own, "plan_basic", days=-1)
    body = call(saas_api, "POST", "/saas/subscriptions/change-plan", catalog.user,
                json={"plan_id": "plan_basic", "billing_cycle": "monthly"})
    assert body["data"]["has_active_subscription"] is True


@pytest.mark.parametrize("case", ["same_plan", "downgrade_over_limit", "unknown_plan", "not_admin"])
def test_change_plan_rejections_leave_subscription_untouched(saas_api, api_db, catalog, case):
    from app.models.branch import Branch
    from app.schemas.enums import RolEnum

    own = catalog.own.tenant
    user, code, plan_id = catalog.user, 400, "plan_basic"
    if case == "same_plan":
        plan_of(api_db, own, "plan_basic")
        message = "Tu empresa ya tiene activo el plan Básico con esta facturación."
    elif case == "downgrade_over_limit":
        api_db.add(Branch(name="A3", city="City", tenant_id=own.id))
        api_db.commit()
        message = "No podés cambiar al plan Básico: tenés 3 sucursales y permite 2."
    elif case == "unknown_plan":
        plan_id, message = "plan_gold", "El plan seleccionado no se encuentra disponible."
    else:
        user = make_user(api_db, RolEnum.encargado, own, catalog.branches[0])
        code, message = 403, "No tienes permisos para acceder a este recurso"
    before = subscriptions(api_db, own)
    body = call(saas_api, "POST", "/saas/subscriptions/change-plan", user, code,
                json={"plan_id": plan_id, "billing_cycle": "monthly"})
    assert body["message"] == message
    assert subscriptions(api_db, own) == before


def test_suspended_company_blocks_staff_and_hides_catalog(saas_api, api_db, catalog):
    own = catalog.own.tenant
    api_db.execute(text("UPDATE tenants SET status = 'suspended' WHERE id = :id"), {"id": own.id})
    api_db.commit()
    body = call(saas_api, "GET", "/saas/subscriptions/current", catalog.user, 403)
    assert body["message"] == "La empresa está suspendida. Contactá al administrador de la plataforma."
    listed = {row["id"] for row in call(saas_api, "GET", "/catalog/products")["data"]}
    assert str(catalog.own.product.id) not in listed and str(catalog.foreign.product.id) in listed
    call(saas_api, "GET", f"/catalog/products/{catalog.own.product.id}", code=404)


def test_try_on_follows_the_selling_company_plan(saas_api, api_db, catalog, monkeypatch):
    from app.routes import garment_routes
    from app.schemas.enums import RolEnum

    async def fake_garment(url):
        return {"image_data_url": "data:image/png;base64,AA==", "mime_type": "image/png"}

    monkeypatch.setattr(garment_routes, "generate_catalog_garment", fake_garment)
    plan_of(api_db, catalog.own.tenant, "plan_basic")  # foreign keeps Enterprise
    catalog.own.variant.image_url = "https://example.invalid/own.png"
    catalog.foreign.variant.image_url = "https://example.invalid/foreign.png"
    api_db.commit()
    listed = {row["id"]: row["try_on_enabled"] for row in call(saas_api, "GET", "/catalog/products")["data"]}
    assert listed[str(catalog.own.product.id)] is False
    assert listed[str(catalog.foreign.product.id)] is True
    client = make_user(api_db, RolEnum.cliente, email="client@example.com")
    blocked = call(saas_api, "POST", "/catalog/garment", client, 403,
                   json={"source_url": "https://example.invalid/own.png"})
    assert blocked["message"] == "Esta tienda no tiene el vestidor virtual incluido en su plan"
    call(saas_api, "POST", "/catalog/garment", client, json={"source_url": "https://example.invalid/foreign.png"})
    call(saas_api, "POST", "/catalog/garment", client, 404, json={"source_url": "https://example.invalid/other.png"})


def test_chatbot_only_recommends_companies_whose_plan_includes_it(api_db, catalog):
    from app.services.chatbot_service import _catalog_candidates

    plan_of(api_db, catalog.own.tenant, "plan_basic")
    products = {row["product_id"] for row in _catalog_candidates(api_db)}
    assert products == {str(catalog.foreign.product.id)}


NEW_PLAN = {
    "name": "Boutique", "slug": "boutique", "description": "Para tiendas pequeñas.",
    "price_monthly": 79, "price_yearly": 790, "max_branches": 3, "max_garments": 1000,
    "features": ["catalog", "pos", "inventory", "chatbot"],
}


def plan_ids(api, user=None, path="/saas/plans"):
    return [plan["id"] for plan in call(api, "GET", path, user)["data"]]


def test_superadmin_creates_plan_shown_publicly_by_price(saas_api, api_db, catalog):
    from app.schemas.enums import RolEnum

    superadmin = make_user(api_db, RolEnum.superadministrador)
    body = call(saas_api, "POST", "/saas/plans", superadmin, 201, json=NEW_PLAN)
    assert body["message"] == "Plan creado exitosamente"
    assert body["data"]["id"] == "plan_boutique" and body["data"]["features"] == NEW_PLAN["features"]
    assert plan_ids(saas_api) == ["plan_basic", "plan_boutique", "plan_pro", "plan_enterprise"]


@pytest.mark.parametrize("case", ["company_admin", "duplicate_slug", "unknown_feature", "invalid_limit"])
def test_plan_creation_rejections_insert_nothing(saas_api, api_db, catalog, case):
    from app.schemas.enums import RolEnum

    user = make_user(api_db, RolEnum.superadministrador)
    payload, code = dict(NEW_PLAN), 400
    if case == "company_admin":
        user, code, message = catalog.user, 403, "No tienes permisos para acceder a este recurso"
    elif case == "duplicate_slug":
        payload["slug"], code, message = "pro", 409, "Ya existe un plan con el identificador 'pro'."
    elif case == "unknown_feature":
        payload["features"] = ["catalog", "teleport"]
        message = "Funciones de plan desconocidas: teleport"
    else:
        payload["max_branches"], code, message = 0, 422, None
    body = call(saas_api, "POST", "/saas/plans", user, code, json=payload)
    if message:
        assert body["message"] == message
    assert api_db.execute(text("SELECT count(*) FROM saas_plans")).scalar_one() == 3


def test_superadmin_edits_and_deactivates_plan_without_breaking_subscribers(saas_api, api_db, catalog):
    from app.schemas.enums import RolEnum

    superadmin = make_user(api_db, RolEnum.superadministrador)
    plan_of(api_db, catalog.own.tenant, "plan_pro")
    body = call(saas_api, "PATCH", "/saas/plans/plan_pro", superadmin,
                json={"price_monthly": 139, "max_branches": 6, "features": ["catalog", "chatbot"]})
    assert body["message"] == "Plan actualizado exitosamente"
    assert (body["data"]["price_monthly"], body["data"]["max_branches"]) == (139, 6)
    assert body["data"]["features"] == ["catalog", "chatbot"] and body["data"]["slug"] == "pro"

    call(saas_api, "PATCH", "/saas/plans/plan_pro", superadmin, json={"is_active": False})
    assert "plan_pro" not in plan_ids(saas_api)
    assert "plan_pro" in plan_ids(saas_api, superadmin, "/saas/plans/admin")
    # The current subscriber keeps its plan; nobody can switch into it anymore.
    current = call(saas_api, "GET", "/saas/subscriptions/current", catalog.user)["data"]
    assert current["plan"]["id"] == "plan_pro" and current["usage"]["branches_max"] == 6
    plan_of(api_db, catalog.foreign.tenant, "plan_basic")
    foreign_admin = make_user(api_db, RolEnum.administrador, catalog.foreign.tenant, email="b@example.com")
    rejected = call(saas_api, "POST", "/saas/subscriptions/change-plan", foreign_admin, 400,
                    json={"plan_id": "plan_pro", "billing_cycle": "monthly"})
    assert rejected["message"] == "El plan seleccionado no se encuentra disponible."


def test_plan_admin_routes_reject_unknown_plan_and_company_admin(saas_api, api_db, catalog):
    from app.schemas.enums import RolEnum

    superadmin = make_user(api_db, RolEnum.superadministrador)
    body = call(saas_api, "PATCH", "/saas/plans/plan_gold", superadmin, 404, json={"price_monthly": 1})
    assert body["message"] == "Plan no encontrado."
    call(saas_api, "GET", "/saas/plans/admin", catalog.user, 403)
