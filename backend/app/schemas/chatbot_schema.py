from enum import Enum
from typing import Any
from uuid import UUID

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ChatIntent(str, Enum):
    CATALOGO = "CATALOGO"
    PEDIDOS = "PEDIDOS"
    POLITICAS = "POLITICAS"
    USO_SISTEMA = "USO_SISTEMA"


class ConversationTurn(BaseModel):
    role: str
    content: str = Field(min_length=1, max_length=400)

    @field_validator("role")
    @classmethod
    def role_must_be_valid(cls, value: str) -> str:
        if value not in {"user", "assistant"}:
            raise ValueError("role must be user or assistant")
        return value

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content must not be blank")
        return value

    model_config = {"extra": "forbid"}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)

    model_config = {"extra": "forbid"}

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be blank")
        return value



class ChatMessageRead(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime
    metadata: Any | None = Field(default=None, validation_alias="message_data", serialization_alias="metadata")

    model_config = {"from_attributes": True}


class BodyProfileRead(BaseModel):
    id: UUID
    user_id: UUID
    top_size: str | None = None
    bottom_size: str | None = None
    shoe_size: str | None = None
    body_shape: str | None = None
    fit_preference: str | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}
