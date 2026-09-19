import asyncio

import pytest

from app.services import catalog_garment_service
from app.services.catalog_garment_service import CatalogGarmentError, _validate_source_url


def test_generate_catalog_garment_returns_source_png_without_gemini(monkeypatch):
    source_bytes = b"\x89PNG\r\n\x1a\nunchanged"
    monkeypatch.setattr(
        catalog_garment_service,
        "_read_source_image",
        lambda source_url: (source_bytes, "image/png"),
    )
    monkeypatch.setattr(catalog_garment_service.settings, "gemini_api_key", None)

    result = asyncio.run(catalog_garment_service.generate_catalog_garment("https://cdn.example/garment.png"))

    assert result == {
        "image_data_url": "data:image/png;base64,iVBORw0KGgp1bmNoYW5nZWQ=",
        "mime_type": "image/png",
    }


def test_validate_source_url_rejects_malformed_urls():
    with pytest.raises(CatalogGarmentError, match="URL de la imagen no es válida"):
        _validate_source_url("https://[")
