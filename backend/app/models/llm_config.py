"""
大模型配置模型
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class LLMConfig(Base):
    """LLM 模型配置表"""
    __tablename__ = "llm_configs"

    config_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_name = Column(String(50), nullable=False, comment="提供商名称: deepseek/kimi/minimax")
    display_name = Column(String(100), nullable=True, comment="显示名称")
    api_key = Column(String(500), nullable=False, comment="API Key (加密存储)")
    base_url = Column(String(500), nullable=False, comment="API Base URL")
    model_version = Column(String(100), nullable=False, comment="默认模型版本")
    is_enabled = Column(Integer, default=1, comment="是否启用")
    priority = Column(Integer, default=0, comment="优先级(数字越小越优先)")
    description = Column(Text, nullable=True, comment="备注说明")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
