"""
多租户模型
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Enum as SAEnum, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class SubscriptionPlan(str, enum.Enum):
    FREE = "FREE"
    ANNUAL = "ANNUAL"


class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agency_name = Column(String(255), nullable=False, comment="代理机构名称")
    uscc = Column(String(50), nullable=True, comment="统一社会信用代码")
    legal_representative = Column(String(100), nullable=True, comment="法定代表人")
    registered_address = Column(Text, nullable=True, comment="注册地址")
    subscription_plan = Column(
        SAEnum(SubscriptionPlan),
        default=SubscriptionPlan.FREE,
        nullable=False,
        comment="订阅计划",
    )
    subscription_expiry = Column(DateTime, nullable=True, comment="年费过期时间")
    balance_credits = Column(Integer, default=0, comment="项目点数余额")
    contact_email = Column(String(255), nullable=True, comment="联系邮箱")
    contact_phone = Column(String(50), nullable=True, comment="联系电话")
    is_active = Column(Integer, default=1, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    users = relationship("User", back_populates="tenant", lazy="selectin")
    projects = relationship(
        "ProjectInvestment", back_populates="tenant", lazy="selectin"
    )
    billing_logs = relationship("BillingLog", back_populates="tenant", lazy="selectin")
    departments = relationship("Department", back_populates="tenant", lazy="selectin")
    approval_flows = relationship(
        "ApprovalFlow", back_populates="tenant", lazy="selectin"
    )
    remittance_records = relationship(
        "RemittanceRecord", back_populates="tenant", lazy="selectin"
    )
    declaration_records = relationship(
        "DeclarationRecord", back_populates="tenant", lazy="selectin"
    )
