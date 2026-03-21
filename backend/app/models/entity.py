"""
境内外主体模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class EntityDomestic(Base):
    """境内主体信息"""
    __tablename__ = "entities_domestic"

    entity_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    company_name = Column(String(255), nullable=False, comment="企业名称")
    uscc = Column(String(50), nullable=False, unique=True, comment="统一社会信用代码")
    industry_code = Column(String(50), nullable=True, comment="境内行业分类代码")
    net_assets = Column(Numeric(20, 2), nullable=True, comment="最近一年净资产")
    net_profit = Column(Numeric(20, 2), nullable=True, comment="最近一年净利润")
    legal_representative = Column(String(100), nullable=True, comment="法定代表人")
    registered_address = Column(Text, nullable=True, comment="注册地址")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    projects = relationship("ProjectInvestment", back_populates="domestic_entity", lazy="selectin")


class EntityOverseas(Base):
    """境外投资标的信息"""
    __tablename__ = "entities_overseas"

    entity_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    overseas_name_cn = Column(String(255), nullable=False, comment="境外企业中文名")
    overseas_name_en = Column(String(255), nullable=True, comment="境外企业英文名")
    target_country = Column(String(100), nullable=False, comment="投资目的国/地区")
    overseas_industry_code = Column(String(50), nullable=True, comment="境外主营业务代码")
    registered_capital = Column(Numeric(20, 2), nullable=True, comment="注册资本/股本")
    currency = Column(String(10), default="USD", comment="注册资本币种")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    projects = relationship("ProjectInvestment", back_populates="overseas_entity", lazy="selectin")
