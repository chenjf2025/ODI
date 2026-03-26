"""
系统日志模型
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class SystemLog(Base):
    __tablename__ = "system_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)

    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=True)
    resource_id = Column(String(100), nullable=True)

    detail = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.now)
