"""
敏感词库模型
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Integer,
    Text,
    Enum as SAEnum,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import enum


class SensitiveLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SensitiveWord(Base):
    __tablename__ = "sensitive_words"

    word_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False
    )

    word_text = Column(String(100), nullable=False)
    word_type = Column(String(50), nullable=False)
    level = Column(
        SAEnum(SensitiveLevel), nullable=False, default=SensitiveLevel.MEDIUM
    )

    description = Column(Text, nullable=True)
    is_active = Column(Integer, default=1)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
