"""Admin branch panel: the administrator lists the orders of ONE branch of their company, never another company's."""
from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_marketplace_transactions import add, call, checkout, market, market_api, rejected  # noqa: F401


def test_admin_sees_only_the_orders_of_the_branch_it_enters(market_api, api_db, market):
    add(market_api, market)
    order = checkout(market_api, market)
    admin = market.staff[0, "administrador"]
    branch0 = call(market_api, admin, "GET", "/orders/branch", params={"branch_id": str(market.branches[0].id)})
    assert [row["id"] for row in branch0] == [order["id"]]
    assert branch0[0]["pickup_code"] is None  # staff never read the customer's pickup code
    assert call(market_api, admin, "GET", "/orders/branch", params={"branch_id": str(market.branches[1].id)}) == []
    rejected(market_api, api_db, admin, "GET", "/orders/branch", 404, "Sucursal no encontrada",
             params={"branch_id": str(market.branches[2].id)})  # another company's branch
    rejected(market_api, api_db, admin, "GET", "/orders/branch", 422, "branch_id es requerido")


def test_manager_never_sees_documents_received_by_another_branch(market_api, api_db, market):
    from app.models.rpa_ingest_job import RpaIngestJob
    from app.routes import rpa_ingest_routes

    market_api.app.include_router(rpa_ingest_routes.router, prefix="/api")
    tenant = market.own.tenant.id
    uploader = market.staff[0, "administrador"].id
    rows = {name: RpaIngestJob(tenant_id=tenant, uploaded_by=uploader, filename=f"{name}.pdf", mime_type="application/pdf",
                               status=status, extracted_items=[], target_branch_id=branch)
            for name, status, branch in (("pending", "completed", None), ("mine", "committed", market.branches[1].id),
                                         ("other", "committed", market.branches[0].id))}
    api_db.add_all(rows.values())
    api_db.commit()
    manager = market.staff[1, "encargado"]
    assert {job["filename"] for job in call(market_api, manager, "GET", "/rpa/ingest/jobs")} == {"pending.pdf", "mine.pdf"}
    rejected(market_api, api_db, manager, "GET", f"/rpa/ingest/jobs/{rows['other'].id}", 404, "Documento no encontrado")
    admin = market.staff[0, "administrador"]
    assert len(call(market_api, admin, "GET", "/rpa/ingest/jobs")) == 3  # the company admin sees every branch


def test_cross_branch_expert_replenishment_is_only_for_the_company_admin(market_api, api_db, market):
    from app.routes import expert_replenishment_routes

    market_api.app.include_router(expert_replenishment_routes.router, prefix="/api")
    for role in ("encargado", "cajero"):
        rejected(market_api, api_db, market.staff[0, role], "POST", "/inventory/expert-replenishment/evaluate", 403,
                 "No tienes permisos para acceder a este recurso")
    call(market_api, market.staff[0, "administrador"], "POST", "/inventory/expert-replenishment/evaluate")
