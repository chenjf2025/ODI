"""
对外申报记录模型
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    Enum as SAEnum,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class DeclarationStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DeclarationTarget(str, enum.Enum):
    NDRC = "NDRC"
    MOFCOM = "MOFCOM"
    SAFE = "SAFE"


class DeclarationRecord(Base):
    __tablename__ = "declaration_records"

    record_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects_investment.project_id"), nullable=False
    )
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False
    )

    target = Column(SAEnum(DeclarationTarget), nullable=False)
    status = Column(
        SAEnum(DeclarationStatus), nullable=False, default=DeclarationStatus.PENDING
    )

    receipt_no = Column(String(100), nullable=True)
    receipt_data = Column(JSON, nullable=True)

    submitted_by = Column(UUID(as_uuid=True), nullable=False)
    submitted_at = Column(DateTime, nullable=True)

    remark = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    project = relationship("ProjectInvestment", back_populates="declaration_records")
    tenant = relationship("Tenant", back_populates="declaration_records")
