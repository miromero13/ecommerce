"""CU10 RPA with AI (intelligent document processing).

A supplier (or company staff) uploads a delivery note / invoice (PDF or image).
Gemini reads it into garment lines; SKUs are matched against the company's catalog;
staff review the draft and a manager or administrator commits it as one stock income.
Unknown SKUs are reported, never created automatically."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Callable
from uuid import UUID

from pydantic import BaseModel, ValidationError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.product_variant import ProductVariant
from app.models.rpa_ingest_job import RpaIngestJob
from app.schemas.catalog_enums import ProductStatusEnum
from app.schemas.enums import RolEnum
from app.schemas.inventory_schema import InventoryMovementCreate
from app.schemas.rpa_ingest_schema import ExtractedItem
from app.services.inventory_service import _add_stock

ALLOWED_TYPES = {"application/pdf", "image/png", "image/jpeg", "image/webp"}
MAX_BYTES = 10 * 1024 * 1024
NO_ITEMS = "No se pudieron reconocer ítems válidos en el documento suministrado"
PROMPT = (
    "Eres un asistente de recepción de mercadería de una tienda de ropa. Lee el documento adjunto "
    "(nota de remisión, factura o catálogo) y devuelve SOLO las líneas de prendas con: sku (código del "
    "artículo tal como aparece), name, size (talla), color, quantity (unidades, entero positivo) y "
    "unit_cost (costo unitario, número). Ignora totales, impuestos, datos del proveedor y del cliente."
)


class JobConflict(RuntimeError):
    pass


class _GeminiLine(BaseModel):
    """Plain JSON types for Gemini's response schema; validated afterwards with ExtractedItem."""
    sku: str
    name: str
    size: str | None = None
    color: str | None = None
    quantity: int
    unit_cost: float | None = None


def validate_upload(content: bytes, content_type: str | None) -> None:
    if content_type not in ALLOWED_TYPES:
        raise ValueError("El archivo proporcionado no es un documento PDF o imagen válido")
    if not content:
        raise ValueError("El archivo proporcionado está vacío")
    if len(content) > MAX_BYTES:
        raise ValueError("El documento no puede superar los 10 MB")


def create_job(db: Session, *, tenant_id: UUID, user_id: UUID, filename: str, content_type: str) -> RpaIngestJob:
    job = RpaIngestJob(tenant_id=tenant_id, uploaded_by=user_id, filename=filename[:255] or "documento",
                       mime_type=content_type, status="processing", extracted_items=[])
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def extract_items(content: bytes, mime_type: str) -> list[dict]:
    """Gemini multimodal extraction with a fixed JSON schema (replaced by a fake in tests)."""
    if not settings.gemini_api_key:
        raise RuntimeError("Gemini no está configurado")
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    result = client.models.generate_content(
        model=settings.gemini_model,
        contents=[types.Part.from_bytes(data=content, mime_type=mime_type), PROMPT],
        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=list[_GeminiLine]),
    )
    return [item.model_dump(mode="json") for item in (result.parsed or [])]


def _match(db: Session, tenant_id: UUID, items: list[ExtractedItem]) -> list[dict]:
    """Attach the company's active variant for each SKU (case-insensitive)."""
    skus = {item.sku.strip().upper() for item in items}
    variants = dict(db.query(func.upper(ProductVariant.sku), ProductVariant.id).filter(
        ProductVariant.tenant_id == tenant_id, ProductVariant.status == ProductStatusEnum.active,
        func.upper(ProductVariant.sku).in_(skus)).all())
    matched = []
    for item in items:
        variant_id = variants.get(item.sku.strip().upper())
        matched.append({**item.model_dump(mode="json"), "sku": item.sku.strip(),
                        "variant_id": str(variant_id) if variant_id else None, "recognized": variant_id is not None})
    return matched


def _valid_items(raw: list[dict]) -> list[ExtractedItem]:
    items = []
    for row in raw:
        try:
            items.append(ExtractedItem.model_validate(row))
        except ValidationError:
            continue  # a malformed line from the document is dropped, not fatal
    return items


def process_job(session_factory: Callable[[], Session], job_id: UUID, content: bytes) -> None:
    """Background task: runs after the 202 response with its own session."""
    with session_factory() as db:
        job = db.query(RpaIngestJob).filter(RpaIngestJob.id == job_id).one()
        try:
            items = _valid_items(extract_items(content, job.mime_type))
            if items:
                job.extracted_items, job.status, job.error_message = _match(db, job.tenant_id, items), "completed", None
            else:
                job.status, job.error_message = "failed", NO_ITEMS
        except Exception:
            # Keep provider/AI details out of the response; the job simply fails.
            job.status, job.error_message = "failed", "No se pudo procesar el documento con IA. Intenta nuevamente."
        db.commit()


def get_job(db: Session, job_id: UUID, *, tenant_id: UUID, user_id: UUID, rol: str) -> RpaIngestJob:
    query = db.query(RpaIngestJob).filter(RpaIngestJob.id == job_id, RpaIngestJob.tenant_id == tenant_id)
    if rol == RolEnum.proveedor.value:
        query = query.filter(RpaIngestJob.uploaded_by == user_id)  # suppliers only see their own documents
    job = query.first()
    if not job:
        raise LookupError("Documento no encontrado")
    return job


def list_jobs(db: Session, *, tenant_id: UUID, user_id: UUID, rol: str) -> list[RpaIngestJob]:
    query = db.query(RpaIngestJob).filter(RpaIngestJob.tenant_id == tenant_id)
    if rol == RolEnum.proveedor.value:
        query = query.filter(RpaIngestJob.uploaded_by == user_id)
    return query.order_by(RpaIngestJob.created_at.desc()).limit(50).all()


def correct_items(db: Session, job: RpaIngestJob, items: list[ExtractedItem]) -> RpaIngestJob:
    if job.status == "committed":
        raise JobConflict("El documento ya fue ingresado al inventario")
    if job.status == "processing":
        raise ValueError("El documento aún se está procesando")
    job.extracted_items, job.status, job.error_message = _match(db, job.tenant_id, items), "completed", None
    db.commit()
    db.refresh(job)
    return job


def commit_job(db: Session, job: RpaIngestJob, *, branch_id: UUID, user_id: UUID) -> dict:
    """All recognized lines enter the branch stock in ONE transaction."""
    if job.status == "committed":
        raise JobConflict("El documento ya fue ingresado al inventario")
    if job.status != "completed":
        raise ValueError("El documento aún no está listo para ingresar al inventario")
    recognized = [item for item in job.extracted_items if item.get("recognized")]
    unrecognized = [item for item in job.extracted_items if not item.get("recognized")]
    if not recognized:
        raise LookupError(NO_ITEMS)
    try:
        for item in recognized:
            _add_stock(db, InventoryMovementCreate(
                variant_id=UUID(item["variant_id"]), branch_id=branch_id, quantity=int(item["quantity"]),
                note=f"Ingesta RPA {job.filename} (costo unitario {Decimal(str(item.get('unit_cost') or 0))})",
            ), user_id, tenant_id=job.tenant_id)
        job.status, job.target_branch_id = "committed", branch_id
        job.committed_by, job.committed_at = user_id, datetime.now(timezone.utc)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"job_id": job.id, "committed_items": len(recognized),
            "committed_units": sum(int(item["quantity"]) for item in recognized),
            "unrecognized_items": unrecognized}


def serialize(job: RpaIngestJob) -> dict:
    return {"job_id": job.id, "filename": job.filename, "status": job.status,
            "extracted_items": job.extracted_items or [], "error_message": job.error_message,
            "target_branch_id": job.target_branch_id, "committed_at": job.committed_at, "created_at": job.created_at}
