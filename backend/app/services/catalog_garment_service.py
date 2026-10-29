from __future__ import annotations

import asyncio
import base64
import ipaddress
import mimetypes
import socket
import ssl
from http.client import HTTPConnection, HTTPSConnection
from pathlib import Path
from urllib.parse import urlsplit

import certifi

from app.core.config import settings

MAX_SOURCE_BYTES = 8 * 1024 * 1024
MAX_URL_LENGTH = 2048
IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
# Local demo catalog served by this backend at /demo-assets (scripts/build_demo_catalog.py --storage local).
DEMO_ASSETS = Path(__file__).resolve().parents[2] / "demo_assets"


class CatalogGarmentError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


class _PinnedHTTPConnection(HTTPConnection):
    def __init__(self, host: str, port: int, resolved_ip: str):
        super().__init__(host, port, timeout=settings.gemini_timeout_seconds)
        self._resolved_ip = resolved_ip

    def connect(self):
        self.sock = socket.create_connection(
            (self._resolved_ip, self.port), self.timeout
        )


class _PinnedHTTPSConnection(HTTPSConnection):
    def __init__(self, host: str, port: int, resolved_ip: str):
        # certifi's bundle, not the OS store: Windows lacks some CDN roots
        # (e.g. GlobalSign ECC used by the catalog images). Still fully verified.
        super().__init__(host, port, timeout=settings.gemini_timeout_seconds,
                         context=ssl.create_default_context(cafile=certifi.where()))
        self._resolved_ip = resolved_ip

    def connect(self):
        sock = socket.create_connection((self._resolved_ip, self.port), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def _validate_source_url(source_url: str) -> str:
    source_url = source_url.strip()
    if len(source_url) > MAX_URL_LENGTH:
        raise CatalogGarmentError(422, "La URL de la imagen es demasiado larga")
    try:
        parsed = urlsplit(source_url)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise CatalogGarmentError(422, "La URL de la imagen no es válida") from exc
    if parsed.scheme not in {"http", "https"} or not hostname or parsed.username or parsed.password:
        raise CatalogGarmentError(422, "La URL de la imagen no es válida")
    try:
        addresses = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except (OSError, ValueError) as exc:
        raise CatalogGarmentError(422, "No se pudo validar el servidor de la imagen") from exc
    if not addresses or any(not ipaddress.ip_address(address[4][0]).is_global for address in addresses):
        raise CatalogGarmentError(422, "La imagen debe estar alojada en un servidor público")
    return source_url


def _resolve_public_address(source_url: str) -> tuple[object, str]:
    parsed = urlsplit(source_url)
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(address[4][0]).is_global for address in addresses):
        raise CatalogGarmentError(422, "La imagen debe estar alojada en un servidor público")
    return parsed, addresses[0][4][0]


def _local_demo_asset(source_url: str) -> tuple[bytes, str] | None:
    """Images of the local demo catalog are read from disk: no network request, so the public-server
    (anti-SSRF) rule below still applies to every other URL. Only image files inside demo_assets qualify."""
    path = urlsplit(source_url).path
    if not path.startswith("/demo-assets/"):
        return None
    file = (DEMO_ASSETS / path.removeprefix("/demo-assets/")).resolve()
    mime_type = mimetypes.guess_type(file.name)[0]
    if DEMO_ASSETS not in file.parents or not file.is_file() or mime_type not in IMAGE_MIME_TYPES:
        return None
    if file.stat().st_size > MAX_SOURCE_BYTES:
        raise CatalogGarmentError(422, "La imagen supera el tamaño máximo permitido")
    return file.read_bytes(), mime_type


def _read_source_image(source_url: str) -> tuple[bytes, str]:
    local = _local_demo_asset(source_url)
    if local:
        return local
    source_url = _validate_source_url(source_url)
    try:
        parsed, resolved_ip = _resolve_public_address(source_url)
    except (OSError, ValueError) as exc:
        raise CatalogGarmentError(422, "No se pudo validar el servidor de la imagen") from exc
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    connection = (
        _PinnedHTTPSConnection(parsed.hostname, port, resolved_ip)
        if parsed.scheme == "https"
        else _PinnedHTTPConnection(parsed.hostname, port, resolved_ip)
    )
    try:
        target = parsed.path or "/"
        if parsed.query:
            target = f"{target}?{parsed.query}"
        host = parsed.hostname
        if parsed.port:
            host = f"{host}:{parsed.port}"
        connection.request(
            "GET",
            target,
            headers={"Host": host, "User-Agent": "ecommerce-catalog-garment/1.0"},
        )
        result = connection.getresponse()
        if 300 <= result.status < 400:
            raise CatalogGarmentError(422, "La URL de la imagen no debe redirigir")
        if result.status >= 400:
            raise CatalogGarmentError(422, "No se pudo descargar la imagen de la prenda")
        content_length = result.getheader("Content-Length")
        if content_length and int(content_length) > MAX_SOURCE_BYTES:
            raise CatalogGarmentError(422, "La imagen supera el tamaño máximo permitido")
        image_bytes = result.read(MAX_SOURCE_BYTES + 1)
        mime_type = result.getheader("Content-Type", "").split(";", 1)[0].lower()
    except CatalogGarmentError:
        raise
    except (OSError, ValueError) as exc:
        raise CatalogGarmentError(422, "No se pudo descargar la imagen de la prenda") from exc
    finally:
        connection.close()

    if len(image_bytes) > MAX_SOURCE_BYTES:
        raise CatalogGarmentError(422, "La imagen supera el tamaño máximo permitido")
    if mime_type not in IMAGE_MIME_TYPES:
        raise CatalogGarmentError(422, "La URL no devuelve una imagen compatible")
    return image_bytes, mime_type


async def generate_catalog_garment(source_url: str) -> dict[str, str]:
    image_bytes, mime_type = await asyncio.to_thread(_read_source_image, source_url)
    return {
        "image_data_url": f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}",
        "mime_type": mime_type,
    }
