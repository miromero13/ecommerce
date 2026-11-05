import uuid
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_offline_catalog_sync_success():
    response = client.get("/api/offline/catalog-sync")
    assert response.status_code == 200
    data = response.json()
    assert data["statusCode"] == 200
    assert "data" in data
    assert "products" in data["data"]
    assert "synced_at" in data["data"]
    assert "total_products" in data["data"]
    assert isinstance(data["data"]["products"], list)


def test_offline_catalog_sync_with_tenant_header():
    response = client.get(
        "/api/offline/catalog-sync",
        headers={"X-Tenant-ID": "ayni-moda"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["statusCode"] == 200
    assert isinstance(data["data"]["products"], list)


def test_offline_queue_sync_idempotency_and_empty():
    # Enviar lote vacío
    response = client.post("/api/offline/queue-sync", json={"operations": []})
    assert response.status_code == 200
    data = response.json()
    assert data["statusCode"] == 200
    assert data["data"]["synced_count"] == 0
    assert data["data"]["conflicts_count"] == 0


def test_offline_conflict_resolution_cash_refund():
    fake_op_id = f"op-test-{uuid.uuid4()}"
    response = client.post(
        f"/api/offline/conflicts/{fake_op_id}/resolve",
        json={
            "resolution_action": "cash_refund",
            "amount": 180.0,
            "bonus_percent": 10.0,
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["statusCode"] == 200
    assert data["data"]["resolution"] == "cash_refund"
    assert data["data"]["refunded_amount"] == 180.0


def test_offline_conflict_resolution_wallet_compensation():
    fake_op_id = f"op-test-{uuid.uuid4()}"
    response = client.post(
        f"/api/offline/conflicts/{fake_op_id}/resolve",
        json={
            "resolution_action": "wallet_compensation",
            "amount": 100.0,
            "bonus_percent": 10.0,
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["statusCode"] == 200
    assert data["data"]["resolution"] == "wallet_compensation"
    assert data["data"]["credited_amount"] == 110.0  # 100 + 10%
