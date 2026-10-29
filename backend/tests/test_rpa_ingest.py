"""CU10: supplier documents (PDF/image) read by Gemini into a stock income draft (Gemini is faked)."""
import pytest
from sqlalchemy import text

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_employee_authorization import headers
from test_marketplace_transactions import call, market, market_api, rejected  # noqa: F401

PDF = b"%PDF-1.4 remito de prueba"


@pytest.fixture
def rpa(market_api, api_db, market, monkeypatch):
    from sqlalchemy.orm import Session
    from app.models.user import User
    from app.routes import rpa_ingest_routes
    from app.schemas.enums import GenderEnum, RolEnum
    from app.services import rpa_ingest_service

    market_api.app.include_router(rpa_ingest_routes.router, prefix="/api")
    # Background processing opens its own session: point it at the test transaction.
    market_api.app.dependency_overrides[rpa_ingest_routes.get_session_factory] = lambda: (
        lambda: Session(bind=api_db.bind, join_transaction_mode="create_savepoint"))
    market.extracted = [
        {"sku": market.own.variant.sku.lower(), "name": "Prenda conocida", "size": "M", "color": "Azul",
         "quantity": 4, "unit_cost": 12.5},
        {"sku": "NO-EXISTE-1", "name": "Prenda nueva", "size": "S", "color": "Rojo", "quantity": 2, "unit_cost": 9},
    ]
    monkeypatch.setattr(rpa_ingest_service, "extract_items", lambda content, mime_type: market.extracted)
    market.supplier = User(name="Proveedor", email="proveedor-rpa@example.com", hashed_password="unused",
                           gender=GenderEnum.femenino, rol=RolEnum.proveedor, tenant_id=market.own.tenant.id,
                           is_active=True)
    api_db.add(market.supplier)
    api_db.commit()
    return market_api


def upload(api, user, content=PDF, content_type="application/pdf", filename="remito.pdf"):
    return api.post("/api/rpa/ingest/upload-document", headers=headers(user),
                    files={"file": (filename, content, content_type)})


def stock(db, market):
    return db.execute(text("SELECT quantity FROM inventory WHERE variant_id = :v AND branch_id = :b"),
                      {"v": market.own.variant.id, "b": market.branches[0].id}).scalar()


def test_supplier_upload_is_extracted_and_skus_are_matched(rpa, api_db, market):
    result = upload(rpa, market.supplier)
    assert result.status_code == 202, result.text
    body = result.json()
    assert body["message"] == "Documento recibido. Extracción RPA en proceso."
    job = call(rpa, market.supplier, "GET", f"/rpa/ingest/jobs/{body['data']['job_id']}")
    assert job["status"] == "completed"
    known, unknown = job["extracted_items"]
    assert (known["recognized"], known["variant_id"]) == (True, str(market.own.variant.id))
    assert (unknown["recognized"], unknown["variant_id"]) == (False, None)


@pytest.mark.parametrize("content, content_type, message", [
    (b"hola", "text/plain", "El archivo proporcionado no es un documento PDF o imagen válido"),
    (PDF + b"0" * (10 * 1024 * 1024), "application/pdf", "El documento no puede superar los 10 MB"),
], ids=["not-a-document", "too-large"])
def test_upload_is_validated(rpa, api_db, market, content, content_type, message):
    result = upload(rpa, market.supplier, content, content_type)
    assert (result.status_code, result.json()["message"]) == (400, message)


def test_document_without_items_fails_with_422(rpa, api_db, market):
    market.extracted = []
    job_id = upload(rpa, market.supplier).json()["data"]["job_id"]
    rejected(rpa, api_db, market.supplier, "GET", f"/rpa/ingest/jobs/{job_id}", 422,
             "No se pudieron reconocer ítems válidos en el documento suministrado")


def test_manager_commits_recognized_items_once(rpa, api_db, market):
    job_id = upload(rpa, market.supplier).json()["data"]["job_id"]
    before = stock(api_db, market)
    rejected(rpa, api_db, market.supplier, "POST", f"/rpa/ingest/jobs/{job_id}/commit", 403,
             json={"branch_id": str(market.branches[0].id)})

    data = call(rpa, market.staff[0, "encargado"], "POST", f"/rpa/ingest/jobs/{job_id}/commit", 201,
                expected_message="Mercadería ingresada al inventario y catálogo sincronizado exitosamente",
                json={"branch_id": str(market.branches[0].id)})
    assert (data["committed_items"], [i["sku"] for i in data["unrecognized_items"]]) == (1, ["NO-EXISTE-1"])
    assert stock(api_db, market) == before + 4
    rejected(rpa, api_db, market.staff[0, "encargado"], "POST", f"/rpa/ingest/jobs/{job_id}/commit", 409,
             "El documento ya fue ingresado al inventario", json={"branch_id": str(market.branches[0].id)})


def test_manager_cannot_commit_to_another_branch(rpa, api_db, market):
    job_id = upload(rpa, market.supplier).json()["data"]["job_id"]
    rejected(rpa, api_db, market.staff[0, "encargado"], "POST", f"/rpa/ingest/jobs/{job_id}/commit", 403,
             "No tienes permisos para esta sucursal", json={"branch_id": str(market.branches[1].id)})


def test_items_can_be_corrected_before_commit(rpa, api_db, market):
    job_id = upload(rpa, market.supplier).json()["data"]["job_id"]
    corrected = call(rpa, market.supplier, "PATCH", f"/rpa/ingest/jobs/{job_id}/items",
                     expected_message="Ítems del documento actualizados",
                     json={"items": [{"sku": market.own.variant.sku, "name": "Prenda", "quantity": 7, "unit_cost": 10}]})
    assert [(i["quantity"], i["recognized"]) for i in corrected["extracted_items"]] == [(7, True)]


def test_other_company_cannot_see_or_commit_the_document(rpa, api_db, market):
    job_id = upload(rpa, market.supplier).json()["data"]["job_id"]
    rejected(rpa, api_db, market.staff[2, "administrador"], "GET", f"/rpa/ingest/jobs/{job_id}", 404,
             "Documento no encontrado")
    rejected(rpa, api_db, market.staff[2, "administrador"], "POST", f"/rpa/ingest/jobs/{job_id}/commit", 404,
             "Documento no encontrado", json={"branch_id": str(market.branches[2].id)})
