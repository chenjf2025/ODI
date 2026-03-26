"""
审批流程模型
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
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"  # 待审批
    APPROVED = "APPROVED"  # 已同意
    REJECTED = "REJECTED"  # 已驳回
    WITHDRAWN = "WITHDRAWN"  # 已撤回


class ApprovalLevel(str, enum.Enum):
    FIRST = "FIRST"  # 初审
    REVIEW = "REVIEW"  # 复核
    FINAL = "FINAL"  # 最终审批


class ApprovalFlow(Base):
    """审批流程表"""

    __tablename__ = "approval_flows"

    flow_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects_investment.project_id"), nullable=False
    )
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False
    )

    current_level = Column(
        SAEnum(ApprovalLevel),
        nullable=False,
        default=ApprovalLevel.FIRST,
        comment="当前审批级别",
    )
    status = Column(
        SAEnum(ApprovalStatus),
        nullable=False,
        default=ApprovalStatus.PENDING,
        comment="审批状态",
    )

    created_by = Column(UUID(as_uuid=True), nullable=False, comment="申请人")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 审批完成后记录
    completed_at = Column(DateTime, nullable=True, comment="审批完成时间")
    completed_by = Column(UUID(as_uuid=True), nullable=True, comment="最终审批人")

    # Relationships
    project = relationship("ProjectInvestment", back_populates="approval_flows")
    tenant = relationship("Tenant", back_populates="approval_flows")
    logs = relationship(
        "ApprovalLog",
        back_populates="flow",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class ApprovalLog(Base):
    """审批日志表"""

    __tablename__ = "approval_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("approval_flows.flow_id", ondelete="CASCADE"),
        nullable=False,
    )

    approver_id = Column(UUID(as_uuid=True), nullable=False, comment="审批人ID")
    level = Column(SAEnum(ApprovalLevel), nullable=False, comment="审批级别")

    action = Column(SAEnum(ApprovalStatus), nullable=False, comment="审批动作")
    opinion = Column(Text, nullable=True, comment="审批意见")

    operator_ip = Column(String(50), nullable=True, comment="操作IP")
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    flow = relationship("ApprovalFlow", back_populates="logs")
