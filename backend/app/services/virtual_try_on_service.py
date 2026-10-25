"""Photo virtual try-on (CU5) through the IDM-VTON Hugging Face Space.

The customer's photo only lives in a temporary directory for the duration of
the call; nothing is stored. The token never leaves the backend.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import mimetypes
import tempfile
from pathlib import Path

from app.core.config import settings
from app.services.catalog_garment_service import CatalogGarmentError, _read_source_image

logger = logging.getLogger(__name__)

MAX_PHOTO_BYTES = 8 * 1024 * 1024
# Magic bytes, so a renamed non-image is rejected regardless of its declared type.
_SIGNATURES = (
    (b"\xff\xd8\xff", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", ".png"),
)
UNAVAILABLE = "El vestidor virtual no está disponible en este momento. Intentá de nuevo en unos minutos."


def photo_suffix(photo: bytes) -> str:
    for signature, suffix in _SIGNATURES:
        if photo.startswith(signature):
            return suffix
    if photo[:4] == b"RIFF" and photo[8:12] == b"WEBP":
        return ".webp"
    raise CatalogGarmentError(422, "La foto debe ser una imagen JPG, PNG o WEBP")


def _run_space(person_path: str, garment_path: str, description: str) -> Path:
    from gradio_client import Client, handle_file

    client = Client(settings.vton_space, token=settings.huggingface_api_token, verbose=False)
    output, _mask = client.predict(
        dict={"background": handle_file(person_path), "layers": [], "composite": None},
        garm_img=handle_file(garment_path),
        garment_des=description,
        is_checked=True,  # let the model build the body mask itself
        is_checked_crop=False,
        denoise_steps=30,
        seed=42,
        api_name="/tryon",
    )
    return Path(output)


async def generate_try_on(photo: bytes, garment_url: str, description: str) -> dict[str, str]:
    if not settings.huggingface_api_token:
        raise CatalogGarmentError(503, "El vestidor virtual no está configurado")
    if not photo:
        raise CatalogGarmentError(422, "Subí o tomá una foto para probarte la prenda")
    if len(photo) > MAX_PHOTO_BYTES:
        raise CatalogGarmentError(422, "La foto supera el tamaño máximo de 8 MB")
    suffix = photo_suffix(photo)
    garment, garment_type = await asyncio.to_thread(_read_source_image, garment_url)

    with tempfile.TemporaryDirectory(prefix="vton-") as folder:
        person_path = Path(folder, "person" + suffix)
        garment_path = Path(folder, "garment" + (mimetypes.guess_extension(garment_type) or ".png"))
        person_path.write_bytes(photo)
        garment_path.write_bytes(garment)
        try:
            output = await asyncio.wait_for(
                asyncio.to_thread(_run_space, str(person_path), str(garment_path), description),
                timeout=settings.vton_timeout_seconds,
            )
            result = output.read_bytes()
        except asyncio.TimeoutError as exc:
            raise CatalogGarmentError(504, "El vestidor tardó demasiado. Intentá de nuevo en unos minutos.") from exc
        except Exception as exc:  # Space asleep, GPU quota exhausted, network...
            logger.warning("Virtual try-on failed: %s: %s", type(exc).__name__, exc)
            raise CatalogGarmentError(503, UNAVAILABLE) from exc

    mime_type = mimetypes.guess_type(output.name)[0] or "image/png"
    return {
        "image_data_url": f"data:{mime_type};base64,{base64.b64encode(result).decode('ascii')}",
        "mime_type": mime_type,
    }
