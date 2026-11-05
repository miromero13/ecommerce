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
