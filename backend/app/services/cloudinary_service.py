from cloudinary import config as cloudinary_config
from cloudinary import uploader

from app.core.config import settings


def _ensure_configured() -> None:
    if not all([settings.cloudinary_cloud_name, settings.cloudinary_api_key, settings.cloudinary_api_secret]):
        raise ValueError("Cloudinary no esta configurado")

    cloudinary_config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )


def upload_image(content: bytes, folder: str, public_id: str | None = None):
    _ensure_configured()

    options = {
        "folder": folder,
        "resource_type": "image",
        "overwrite": True,
        "unique_filename": True,
    }
    if public_id:
        options["public_id"] = public_id

    result = uploader.upload(content, **options)
    return {
        "image_url": result.get("secure_url"),
        "image_public_id": result.get("public_id"),
    }


def delete_image(public_id: str | None) -> None:
    if not public_id:
        return

    _ensure_configured()
    uploader.destroy(public_id, resource_type="image")
