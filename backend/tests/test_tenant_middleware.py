"""CU1 tenant resolution: X-Tenant-ID header or subdomain, never trusted over the JWT."""
import pytest

from test_employee_authorization import headers


def names(response):
    assert response.status_code == 200, response.text
    return sorted(branch["name"] for branch in response.json()["data"])


@pytest.mark.parametrize("ref", ["id", "slug"])
def test_staff_header_matching_own_company_is_accepted(api, identities, ref):
    admin, tenants, _ = identities
    value = str(tenants[0].id) if ref == "id" else tenants[0].slug
    result = api.get("/api/branches/", headers={**headers(admin), "X-Tenant-ID": value})
    assert names(result) == ["A1", "A2"]


def test_staff_header_for_other_company_is_forbidden(api, identities):
    admin, tenants, _ = identities
    result = api.get("/api/branches/", headers={**headers(admin), "X-Tenant-ID": tenants[1].slug})
    assert result.status_code == 403
    assert result.json()["message"] == "El encabezado X-Tenant-ID no corresponde a tu empresa"


def test_unknown_company_header_is_not_found(api, identities):
    result = api.get("/api/branches/public", headers={"X-Tenant-ID": "no-such-company"})
    assert result.status_code == 404
    assert result.json()["message"] == "Empresa no encontrada"


def test_public_storefront_resolves_company_from_header(api, identities):
    _, tenants, _ = identities
    assert names(api.get("/api/branches/public", headers={"X-Tenant-ID": tenants[1].slug})) == ["B1"]
    assert names(api.get("/api/branches/public")) == ["A1", "A2", "B1"]


def test_public_storefront_resolves_company_from_subdomain(api, identities, monkeypatch):
    from app.core.config import settings

    _, tenants, _ = identities
    monkeypatch.setattr(settings, "tenant_base_domain", "plataforma.com")
    result = api.get("/api/branches/public", headers={"Host": f"{tenants[1].slug}.plataforma.com"})
    assert names(result) == ["B1"]
