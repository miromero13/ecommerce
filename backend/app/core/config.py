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
    tenant_base_domain: str | None = None
    # CU20 platform delivery tariff (Bs): base + per km, within a coverage radius.
    delivery_base_fee: float = 8.0
    delivery_fee_per_km: float = 2.5
    delivery_max_km: float = 15.0
    # Simulated QR: sandbox lets the payer confirm from the UI; a real bank uses the secret webhook.
    qr_sandbox: bool = True
    qr_webhook_secret: str | None = None
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"
    gemini_garment_model: str | None = None
    gemini_timeout_seconds: int = Field(default=30, ge=5, le=120)
    # Respaldo opcional de CU08 (reportes): solo traduce frases que el intérprete local no entiende.
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-20b"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_timeout_seconds: int = Field(default=8, ge=2, le=30)
    groq_max_calls_per_tenant_hour: int = Field(default=20, ge=1, le=1000)
    groq_max_calls_per_hour_global: int = Field(default=200, ge=1, le=10000)
    huggingface_api_token: str | None = None
    vton_space: str = "yisol/IDM-VTON"
    vton_timeout_seconds: int = Field(default=120, ge=10, le=300)
    firebase_service_account_path: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "FIREBASE_SERVICE_ACCOUNT_PATH",
            "FIREBASE_SERVICE_ACCOUNT_FILE",
        ),
    )
    app_name: str = "FashionStore SaaS"
    mailer_service: str = "https://send.api.mailtrap.io/api/send"
    mailer_email: str = "no-reply@devhooh.com"
    mailer_secret_key: str | None = None


    class Config:
        env_file = ".env"
settings = Settings()
