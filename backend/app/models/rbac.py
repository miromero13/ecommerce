import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.schemas.enums import RolEnum


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    module = Column(String(50), nullable=False, index=True)
    description = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    code = Column(String(64), nullable=False)
    name = Column(String(100), nullable=False)
    base_rol = Column(SQLAlchemyEnum(RolEnum), nullable=True)
    is_system = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_roles_tenant_code"),
    )

    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    users = relationship("User", secondary=user_roles, back_populates="custom_roles")


from app.models.user import User  # noqa: E402, F401
