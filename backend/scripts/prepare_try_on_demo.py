"""Leaves the 3D fitting rooms (Vestidor 3D) of a company ready to try on, without calibrating by hand.

    python -m scripts.prepare_try_on_demo [--tenant ayni-moda]

1. Every variant without a transparent cut-out (try_on_image_url) gets one: the studio background of its local
   catalog photo (demo_assets/catalog) is removed and saved as demo_assets/try-on/cut_<photo>.png.
2. Every variant without calibration points (garment_points) gets the 17 default points of the 3D engine
   (GARMENT_POINTS in frontend/.../garment-overlay.renderer.ts), so the garment is placed as soon as the
   fitting room opens. Points saved by hand are never overwritten.

Run it again after `python -m scripts.seed_demo --reset`, which recreates the variants without these data.
"""
import argparse
from collections import deque
from pathlib import Path
from urllib.parse import urlsplit

import numpy as np
from PIL import Image

from app.core.database import SessionLocal
import main  # noqa: F401  registers every model and mapper
from app.models.product_variant import ProductVariant
from app.models.tenant import Tenant

ASSETS = Path(__file__).resolve().parents[1] / "demo_assets"
# Same values and order as GARMENT_POINTS (long-sleeve top seen from the front).
DEFAULT_POINTS = [
    (0.27, 0.10), (0.73, 0.10), (0.30, 0.35), (0.70, 0.35), (0.30, 0.94), (0.70, 0.94),
    (0.12, 0.52), (0.27, 0.55), (0.03, 0.95), (0.19, 0.98), (0.88, 0.52), (0.73, 0.55),
    (0.97, 0.95), (0.81, 0.98), (0.42, 0.01), (0.58, 0.01), (0.50, 0.16),
]
# Background removal tolerances (step between neighbours, distance to the border colour).
# Checked one by one on the demo catalog; these two photos need their own values.
TOLERANCE = {
    "vestido_mini_drop_waist_lunares_blanco.jpg": (1, 2),   # white dress on a white background
    "chaqueta_bomber_cuero_vino_cinturon.jpg": (6, 60),     # grey floor shadow under the jacket
}
DEFAULT_TOLERANCE = (3, 20)


def remove_background(source: Path, target: Path) -> None:
    """Grow the background from the image borders: a pixel joins when it is close to the neighbour it is
    reached from (smooth studio gradients) and to the border colour, so the garment itself is never entered."""
    step, far = TOLERANCE.get(source.name, DEFAULT_TOLERANCE)
    rgb = np.asarray(Image.open(source).convert("RGB")).astype(np.int16)
    h, w, _ = rgb.shape
    base = np.median(np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]), axis=0)
    candidate = ((np.abs(rgb - base).max(axis=2) <= far) & ((rgb.max(axis=2) - rgb.min(axis=2)) <= 22))
    background = np.zeros((h, w), bool)
    queue = deque((y, x) for y in range(h) for x in (0, w - 1) if candidate[y, x])
    queue.extend((y, x) for x in range(w) for y in (0, h - 1) if candidate[y, x])
    for y, x in queue:
        background[y, x] = True
    while queue:
        y, x = queue.popleft()
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if (0 <= ny < h and 0 <= nx < w and not background[ny, nx] and candidate[ny, nx]
                    and np.abs(rgb[ny, nx] - rgb[y, x]).max() <= step):
                background[ny, nx] = True
                queue.append((ny, nx))
    alpha = np.where(background, 0, 255).astype(np.uint8)
    Image.fromarray(np.dstack([rgb.astype(np.uint8), alpha]), "RGBA").save(target, optimize=True)


def main_cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tenant", default="ayni-moda", help="slug of the company (default: ayni-moda)")
    args = parser.parse_args()
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.slug == args.tenant).first()
        if not tenant:
            raise SystemExit(f"No existe la empresa {args.tenant}")
        variants = db.query(ProductVariant).filter(ProductVariant.tenant_id == tenant.id).all()
        cutouts, points, skipped = {}, 0, []
        for variant in variants:
            if not variant.try_on_image_url and variant.image_url:
                url = urlsplit(variant.image_url)
                source = ASSETS / url.path.removeprefix("/demo-assets/")
                if not url.path.startswith("/demo-assets/catalog/") or not source.is_file():
                    skipped.append(variant.sku)
                else:
                    name = f"cut_{source.stem}.png"
                    if source.name not in cutouts:
                        target = ASSETS / "try-on" / name
                        if not target.exists():
                            remove_background(source, target)
                        cutouts[source.name] = name
                    variant.try_on_image_url = f"{url.scheme}://{url.netloc}/demo-assets/try-on/{name}"
            if variant.garment_points is None:
                variant.garment_points = [{"x": x, "y": y} for x, y in DEFAULT_POINTS]
                points += 1
        db.commit()
        print(f"{tenant.name}: {len(variants)} variantes, {len(cutouts)} prendas recortadas, "
              f"{points} variantes con puntos de calibración nuevos")
        if skipped:
            print("Sin foto local del catálogo (no se recortaron):", ", ".join(skipped))
    finally:
        db.close()


if __name__ == "__main__":
    main_cli()
