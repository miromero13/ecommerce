from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    access_token_expire_minutes: int
    algorithm: str = "HS256"
    cloudinary_cloud_name: str | None = None
    cloudinary_api_key: str | None = None
    cloudinary_api_secret: str | None = None
    cloudinary_folder: str = "fashionstore"
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_publishable_key: str | None = None
    stripe_currency: str = "usd"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"
    gemini_garment_model: str | None = None
    gemini_timeout_seconds: int = Field(default=30, ge=5, le=120)
    firebase_service_account_path: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "FIREBASE_SERVICE_ACCOUNT_PATH",
            "FIREBASE_SERVICE_ACCOUNT_FILE",
        ),
    )

    class Config:
        env_file = ".env"
settings = Settings()
