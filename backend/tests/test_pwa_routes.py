"""CU22: PWA Web App Manifest endpoint testing."""
import pytest


def test_pwa_manifest_returns_200_and_manifest_structure(api):
    res = api.get("/api/pwa/manifest")
    assert res.status_code == 200
    body = res.json()
    assert body["statusCode"] == 200
    assert "Configuración de manifiesto PWA obtenida" in body["message"]

    manifest = body["data"]
    assert "name" in manifest
    assert "short_name" in manifest
    assert manifest["start_url"] == "/"
    assert manifest["display"] == "standalone"
    assert manifest["background_color"] == "#ffffff"
    assert "theme_color" in manifest
    assert len(manifest["icons"]) >= 2
    sizes = [icon["sizes"] for icon in manifest["icons"]]
    assert "192x192" in sizes
    assert "512x512" in sizes


def test_pwa_manifest_with_tenant_header(api, identities):
    _, tenants, _ = identities
    res = api.get("/api/pwa/manifest", headers={"X-Tenant-ID": tenants[0].slug})
    assert res.status_code == 200
    manifest = res.json()["data"]
    assert manifest["name"] == tenants[0].name
