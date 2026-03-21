"""
动态规则引擎模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Enum as SAEnum, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base
import enum


class RuleType(str, enum.Enum):
    COUNTRY = "COUNTRY"
    INDUSTRY = "INDUSTRY"


class RiskLevel(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RulesEngine(Base):
    """动态规则字典表"""
    __tablename__ = "rules_engine"

    rule_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_type = Column(SAEnum(RuleType), nullable=False, comment="规则类型")
    target_value = Column(String(100), nullable=False, comment="目标值：国家代码或行业名称")
    risk_level = Column(SAEnum(RiskLevel), nullable=False, comment="风险等级")
    rule_name = Column(String(255), nullable=True, comment="规则名称")
    description = Column(Text, nullable=True, comment="规则描述")
    trigger_action = Column(JSONB, nullable=True, comment="命中规则后的动作")
    is_active = Column(Integer, default=1, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
