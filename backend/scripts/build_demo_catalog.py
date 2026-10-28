"""Build the demo catalog from the garment package of the first partial.

Reads PAQUETE_CATALOGO_Y_VESTIDOR_IA, drops the test products (no photo), uploads the catalog photos and the
transparent try-on cut-outs ("rigs"), and writes `scripts/data/demo_catalog.json` (committed).

Storage:
- `--storage local` (default, localhost): copies the images to `backend/demo_assets/` (served at /demo-assets);
  the catalog keeps relative paths and the seed builds the full URL.
- `--storage cloudinary`: uploads them once; the catalog keeps the Cloudinary URLs (for the deployed database).

    python -m scripts.build_demo_catalog --package "<ruta>/PAQUETE_CATALOGO_Y_VESTIDOR_IA" [--storage cloudinary]
"""
import argparse
import json
import shutil
from pathlib import Path

import cloudinary
import cloudinary.uploader

from app.core.config import settings

OUTPUT = Path(__file__).parent / "data" / "demo_catalog.json"
ASSETS = Path(__file__).parents[1] / "demo_assets"


def _store_local(path: Path, folder: str) -> dict:
    target = ASSETS / folder / path.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, target)
    return {"url": f"{folder}/{path.name}", "public_id": None}  # relative: the seed adds the assets base URL


def _upload(path: Path, folder: str) -> dict:
    result = cloudinary.uploader.upload(
        str(path), folder=f"{settings.cloudinary_folder}/demo/{folder}", public_id=path.stem,
        overwrite=True, unique_filename=False, resource_type="image",
    )
    return {"url": result["secure_url"], "public_id": result["public_id"]}


def _first_rig(rigs_dir: Path) -> dict[int, Path]:
    """One transparent cut-out per product (the package has a few duplicated rigs)."""
    rigs: dict[int, Path] = {}
    for png in sorted(rigs_dir.glob("rig_p*.png")):
        product_id = int(png.stem.split("_")[1][1:])
        rigs.setdefault(product_id, png)
    return rigs


def build(package: Path, storage: str = "local") -> dict:
    data = json.loads((package / "01_DATOS_BASE_DE_DATOS" / "catalog_seed_data.json").read_text(encoding="utf-8"))
    photos_dir = package / "02_IMAGENES_CATALOGO" / "products"
    categories = {c["id"]: c["name"] for c in data["categories"]}
    seasons = {s["id"]: s["name"] for s in data["seasons"]}
    colors = {c["id"]: {"name": c["name"], "hex": c["hex_code"]} for c in data["colors"]}
    sizes = {s["id"]: s["name"] for s in data["sizes"]}
    photo_of = {}
    for image in data["product_images"]:
        if image["is_primary"] or image["product_id"] not in photo_of:
            photo_of[image["product_id"]] = Path(image["image_url"]).name
    variants_of: dict[int, list] = {}
    for variant in data["product_variants"]:
        if variant["is_active"]:
            variants_of.setdefault(variant["product_id"], []).append(variant)
    rigs = _first_rig(package / "03_VESTIDOR_VIRTUAL_IA" / "rigs")

    store = _store_local
    if storage == "cloudinary":
        cloudinary.config(cloud_name=settings.cloudinary_cloud_name, api_key=settings.cloudinary_api_key,
                          api_secret=settings.cloudinary_api_secret, secure=True)
        store = _upload
    products = []
    for product in sorted(data["products"], key=lambda p: p["id"]):
        photo = photo_of.get(product["id"])
        variants = variants_of.get(product["id"], [])
        if not photo or not variants or not product["is_active"]:
            continue  # test rows of the package ("Prenda Descontinuada Test", "Falda Basica b3c1"...)
        uploaded = store(photos_dir / photo, "catalog")
        rig = store(rigs[product["id"]], "try-on") if product["id"] in rigs else None
        products.append({
            "key": product["id"],
            "name": product["name"].strip(),
            "description": (product["description"] or "").strip(),
            "price": product["base_price"],
            "compare_at_price": product["compare_at_price"],
            "category": categories[product["category_id"]],
            "season": seasons.get(product["season_id"], "Atemporal / Esenciales"),
            "material": product["material"],
            "tags": [t.strip() for t in (product["tags"] or "").split(",") if t.strip()],
            "image_url": uploaded["url"],
            "image_public_id": uploaded["public_id"],
            "try_on_image_url": rig["url"] if rig else None,
            "variants": [{"color": colors[v["color_id"]]["name"], "size": sizes[v["size_id"]],
                          "price": v["price_override"]} for v in variants],
        })
        print(f"  {product['id']:>3} {product['name'][:60]}{'  + vestidor' if rig else ''}")
    used_colors = {v["color"] for p in products for v in p["variants"]}
    return {
        "source": "primer_parcial.1.0/PAQUETE_CATALOGO_Y_VESTIDOR_IA",
        "storage": storage,
        "colors": [c for c in colors.values() if c["name"] in used_colors],
        "sizes": sorted({v["size"] for p in products for v in p["variants"]}, key=lambda s: list(sizes.values()).index(s)),
        "seasons": list(seasons.values()),
        "categories": sorted({p["category"] for p in products}),
        "products": products,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--storage", choices=("local", "cloudinary"), default="local")
    args = parser.parse_args()
    catalog = build(args.package, args.storage)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(catalog['products'])} prendas -> {OUTPUT}")


if __name__ == "__main__":
    main()
