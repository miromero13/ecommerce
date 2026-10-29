"""The local demo catalog images feed the fitting rooms without weakening the public-server (anti-SSRF) rule."""
import pytest

from app.services.catalog_garment_service import CatalogGarmentError, DEMO_ASSETS, _read_source_image

pytestmark = pytest.mark.skipif(not (DEMO_ASSETS / "try-on").is_dir(), reason="demo_assets not built")


def test_demo_asset_is_read_from_disk_and_traversal_is_refused():
    name = sorted((DEMO_ASSETS / "try-on").iterdir())[0].name
    content, mime = _read_source_image(f"http://localhost:8000/demo-assets/try-on/{name}")
    assert mime == "image/png" and content[:4] == b"\x89PNG"
    for url in ("http://localhost:8000/demo-assets/../main.py", "http://localhost:8000/demo-assets/try-on/nope.png",
                "http://localhost:8000/other/x.png"):
        with pytest.raises(CatalogGarmentError):
            _read_source_image(url)  # falls back to the network rule: localhost is not a public server
