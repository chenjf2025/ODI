"""
部门模型 - 树形结构
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Department(Base):
    """部门表 - 支持树形结构"""

    __tablename__ = "departments"

    department_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False
    )
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("departments.department_id"),
        nullable=True,
        comment="上级部门ID",
    )
    department_name = Column(String(100), nullable=False, comment="部门名称")
    leader_user_id = Column(UUID(as_uuid=True), nullable=True, comment="部门负责人")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Integer, default=1, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    tenant = relationship("Tenant", back_populates="departments")
    parent = relationship("Department", remote_side=[department_id], backref="children")
    users = relationship("User", back_populates="department", lazy="selectin")
