from pydantic import BaseModel, Field, field_validator


class CatalogGarmentRequest(BaseModel):
    source_url: str = Field(min_length=1, max_length=2048)

    model_config = {"extra": "forbid"}

    @field_validator("source_url")
    @classmethod
    def source_url_must_be_http_image_url(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith(("http://", "https://")):
            raise ValueError("La URL de la imagen debe usar http o https")
        return value


class CatalogGarmentResponse(BaseModel):
    image_data_url: str
    mime_type: str
