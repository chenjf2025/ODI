"""
投资项目模型 - 含状态机
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
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ProjectStatus(str, enum.Enum):
    """项目 9 阶段状态机"""

    PRE_REVIEW = "PRE_REVIEW"  # 意向测算与智能预审
    DATA_COLLECTION = "DATA_COLLECTION"  # 立项与自动化材料准备
    NDRC_FILING_PENDING = "NDRC_FILING_PENDING"  # 发改委备案准备
    NDRC_APPROVED = "NDRC_APPROVED"  # 发改委获批
    MOFCOM_FILING_PENDING = "MOFCOM_FILING_PENDING"  # 商务部备案准备
    MOFCOM_APPROVED = "MOFCOM_APPROVED"  # 商务部获批
    BANK_REG_PENDING = "BANK_REG_PENDING"  # 银行外汇登记中
    FUNDS_REMITTED = "FUNDS_REMITTED"  # 资金已汇出
    POST_INVESTMENT = "POST_INVESTMENT"  # 投后存量维系


# 合法的状态转移映射
VALID_TRANSITIONS = {
    ProjectStatus.PRE_REVIEW: [ProjectStatus.DATA_COLLECTION],
    ProjectStatus.DATA_COLLECTION: [ProjectStatus.NDRC_FILING_PENDING],
    ProjectStatus.NDRC_FILING_PENDING: [ProjectStatus.NDRC_APPROVED],
    ProjectStatus.NDRC_APPROVED: [ProjectStatus.MOFCOM_FILING_PENDING],
    ProjectStatus.MOFCOM_FILING_PENDING: [ProjectStatus.MOFCOM_APPROVED],
    ProjectStatus.MOFCOM_APPROVED: [ProjectStatus.BANK_REG_PENDING],
    ProjectStatus.BANK_REG_PENDING: [ProjectStatus.FUNDS_REMITTED],
    ProjectStatus.FUNDS_REMITTED: [ProjectStatus.POST_INVESTMENT],
    ProjectStatus.POST_INVESTMENT: [],
}


class InvestmentCurrency(str, enum.Enum):
    USD = "USD"
    CNY = "CNY"
    HKD = "HKD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    SGD = "SGD"


class InvestmentPath(str, enum.Enum):
    DIRECT = "DIRECT"  # 直接投资
    SPV_HK = "SPV_HK"  # 通过香港 SPV
    SPV_SGP = "SPV_SGP"  # 通过新加坡 SPV
    MULTI_LAYER = "MULTI_LAYER"  # 多层架构


class ProjectInvestment(Base):
    """投资项目业务实体"""

    __tablename__ = "projects_investment"

    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False
    )
    domestic_entity_id = Column(
        UUID(as_uuid=True), ForeignKey("entities_domestic.entity_id"), nullable=True
    )
    overseas_entity_id = Column(
        UUID(as_uuid=True), ForeignKey("entities_overseas.entity_id"), nullable=True
    )

    project_name = Column(String(500), nullable=False, comment="项目自动命名")
    investment_amount = Column(Numeric(20, 2), nullable=True, comment="拟投资总额")
    currency = Column(
        SAEnum(InvestmentCurrency), default=InvestmentCurrency.USD, comment="币种"
    )
    investment_path = Column(
        SAEnum(InvestmentPath), default=InvestmentPath.DIRECT, comment="投资架构"
    )
    funding_source = Column(JSONB, nullable=True, comment="资金来源构成")
    purpose_description = Column(Text, nullable=True, comment="投资必要性说明")
    status = Column(
        SAEnum(ProjectStatus), default=ProjectStatus.PRE_REVIEW, comment="当前状态"
    )

    # AI 生成内容存储
    pre_review_report = Column(JSONB, nullable=True, comment="预审报告 JSON")
    feasibility_report = Column(Text, nullable=True, comment="可研报告内容")
    due_diligence_report = Column(Text, nullable=True, comment="尽调报告内容")

    # 上传文件记录
    uploaded_files = Column(JSONB, default=list, comment="上传文件列表")
    ndrc_certificate_url = Column(
        String(500), nullable=True, comment="发改委备案通知书"
    )
    mofcom_certificate_url = Column(
        String(500), nullable=True, comment="商务部投资证书"
    )

    created_by = Column(UUID(as_uuid=True), nullable=True, comment="创建人")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    tenant = relationship("Tenant", back_populates="projects")
    domestic_entity = relationship("EntityDomestic", back_populates="projects")
    overseas_entity = relationship("EntityOverseas", back_populates="projects")
    billing_logs = relationship("BillingLog", back_populates="project", lazy="selectin")
    status_logs = relationship(
        "ProjectStatusLog",
        back_populates="project",
        lazy="selectin",
        passive_deletes="all",
    )
    documents = relationship(
        "ProjectDocument",
        back_populates="project",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class ProjectStatusLog(Base):
    """项目状态流转日志"""

    __tablename__ = "project_status_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects_investment.project_id", ondelete="CASCADE"),
        nullable=False,
    )
    from_status = Column(SAEnum(ProjectStatus), nullable=True)
    to_status = Column(SAEnum(ProjectStatus), nullable=False)
    operator_id = Column(UUID(as_uuid=True), nullable=True, comment="操作人")
    remark = Column(Text, nullable=True, comment="备注")
    created_at = Column(DateTime, default=datetime.now)

    project = relationship("ProjectInvestment", back_populates="status_logs")
