"""
导出字段模板模型 - 支持发改委/商务部导出字段映射配置化
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class TemplateType(str, enum.Enum):
    NDRC = "NDRC"
    MOFCOM = "MOFCOM"


class ExportTemplate(Base):
    """导出字段模板表 - 支持发改委 XML 和商务部 Excel 字段映射配置"""

    __tablename__ = "export_templates"

    template_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_type = Column(
        SAEnum(TemplateType), nullable=False, comment="模板类型: NDRC/MOFCOM"
    )
    column_index = Column(Integer, nullable=False, comment="字段顺序位置")
    xml_tag = Column(String(100), nullable=True, comment="XML标签名 (NDRC用)")
    display_name = Column(String(200), nullable=False, comment="显示名称 (表头)")
    data_key = Column(String(100), nullable=False, comment="数据字段名")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
