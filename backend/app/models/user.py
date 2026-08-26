# ✅ app/models/user.py
from sqlalchemy import Column, String, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from app.schemas.enums import RolEnum, GenderEnum
from app.core.database import Base  # 👈 USA EL MISMO Base
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    gender = Column(SQLAlchemyEnum(GenderEnum), nullable=False)
    rol = Column(SQLAlchemyEnum(RolEnum), nullable=False)
