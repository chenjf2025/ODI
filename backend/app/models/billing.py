"""
计费流水模型
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Numeric,
    Enum as SAEnum,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class BillingType(str, enum.Enum):
    PROJECT_DEDUCTION = "PROJECT_DEDUCTION"  # 工单扣点
    ANNUAL_RENEWAL = "ANNUAL_RENEWAL"  # 年费充值
    CREDIT_TOPUP = "CREDIT_TOPUP"  # 点数充值


class BillingLog(Base):
    """计费流水表"""

    __tablename__ = "billing_logs"

    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False
    )
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects_investment.project_id"), nullable=True
    )
    billing_type = Column(SAEnum(BillingType), nullable=False, comment="计费类型")
    credits_changed = Column(Integer, default=0, comment="点数变动")
    amount = Column(Numeric(12, 2), default=0, comment="金额变动")
    balance_after = Column(Integer, default=0, comment="变动后余额")
    prompt_tokens = Column(Integer, nullable=True, comment="输入token数")
    completion_tokens = Column(Integer, nullable=True, comment="输出token数")
    total_tokens = Column(Integer, nullable=True, comment="总token数")
    remark = Column(Text, nullable=True, comment="备注")
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    tenant = relationship("Tenant", back_populates="billing_logs")
    project = relationship("ProjectInvestment", back_populates="billing_logs")
