"""
登录日志模型
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class LoginLog(Base):
    __tablename__ = "login_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=True
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)

    username = Column(String(100), nullable=False)
    login_status = Column(String(20), nullable=False)
    fail_reason = Column(String(255), nullable=True)

    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    login_method = Column(String(20), default="PASSWORD")

    created_at = Column(DateTime, default=datetime.now)
