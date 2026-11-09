from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.tenant import Tenant
from app.utils.response import response

router = APIRouter(prefix="/pwa", tags=["PWA"])


# [CU22 - Secuencia: Paso 1.1] PwaService llama a get_pwa_manifest(raw) de pwa_routes (GET /api/pwa/manifest.json)
@router.get("/manifest")
@router.get("/manifest.json")
def get_pwa_manifest(request: Request, raw: bool = False, db: Session = Depends(get_db)):
    """Returns dynamic Web App Manifest configuration based on active tenant."""
    tenant_ref = getattr(request.state, "tenant_ref", None)
    tenant: Tenant | None = None

    if tenant_ref:
        is_uuid = False
        try:
            val = uuid.UUID(str(tenant_ref))
            is_uuid = True
        except (ValueError, AttributeError):
            is_uuid = False

        if is_uuid:
            # [CU22 - Secuencia: Pasos 1.2, 1.4] pwa_routes ejecuta select(Tenant) sobre la entidad Empresa
            tenant = db.scalars(select(Tenant).where(Tenant.id == val)).first()
        else:
            tenant = db.scalars(select(Tenant).where(Tenant.slug == str(tenant_ref))).first()

    # If tenant_ref is present, brand by tenant; otherwise brand as global FashionStore marketplace
    if tenant:
        name = tenant.name
        short_name = tenant.slug.capitalize() if tenant.slug else name.split()[0]
        theme_color = tenant.primary_color if tenant.primary_color else "#111827"
        logo = tenant.logo_url
        description = f"Plataforma omnicanal de moda y compras para {name}."
    else:
        name = "FashionStore"
        short_name = "FashionStore"
        theme_color = "#111827"
        logo = None
        description = "Plataforma omnicanal de moda y compras para marcas exclusivas."

    icons = [
        {
            "src": logo if logo else "/icons/icon-192x192.png",
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "any maskable"
        },
        {
            "src": logo if logo else "/icons/icon-512x512.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "any maskable"
        }
    ]

    manifest_data = {
        "name": name,
        "short_name": short_name,
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": theme_color,
        "orientation": "portrait-primary",
        "scope": "/",
        "description": description,
        "icons": icons
    }

    if raw or "manifest" in request.headers.get("accept", "").lower() or request.url.path.endswith(".json"):
        return JSONResponse(content=manifest_data, media_type="application/manifest+json")

    return response(
        status_code=200,
        message="Configuración de manifiesto PWA obtenida",
        data=manifest_data
    )
