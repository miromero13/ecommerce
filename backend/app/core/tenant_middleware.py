from fastapi import FastAPI, Request

from app.core.config import settings

IGNORED_SUBDOMAINS = {"www", "api"}


def tenant_ref_from_request(request: Request) -> str | None:
    """Company reference sent by the client: X-Tenant-ID (id or slug) or {slug}.<tenant_base_domain>."""
    header = request.headers.get("x-tenant-id", "").strip()
    if header:
        return header
    base = settings.tenant_base_domain
    host = request.headers.get("host", "").split(":")[0].lower()
    if base and host.endswith("." + base):
        subdomain = host[: -len(base) - 1]
        if subdomain and subdomain not in IGNORED_SUBDOMAINS:
            return subdomain
    return None


def register_tenant_middleware(app: FastAPI) -> None:
    # Only extracts the reference; app.auth.dependencies validates it against the DB and the JWT.
    @app.middleware("http")
    async def resolve_tenant(request: Request, call_next):
        request.state.tenant_ref = tenant_ref_from_request(request)
        return await call_next(request)
