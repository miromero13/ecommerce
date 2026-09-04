from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
import uuid


class Branch(Base):
    __tablename__ = "branches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False, unique=True)
    city = Column(String, nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)
