"""
用户模型 - 含角色权限
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Enum as SAEnum, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    CLIENT_USER = "CLIENT_USER"
    OPERATOR = "OPERATOR"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False
    )
    department_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.department_id"),
        nullable=True,
        comment="部门ID",
    )
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True, comment="手机号")
    role = Column(SAEnum(UserRole), default=UserRole.CLIENT_USER, nullable=False)
    is_active = Column(Integer, default=1, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    department = relationship("Department", back_populates="users")
