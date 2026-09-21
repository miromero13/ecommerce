from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    title: str
    body: str
    data: dict[str, Any] = Field(default_factory=dict)
    read_at: datetime | None = None
    created_at: datetime


class DeviceTokenUpsert(BaseModel):
    token: str = Field(min_length=1, max_length=4096)
    platform: Literal["android"] = "android"
