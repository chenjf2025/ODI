"""
数据字典模型
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class DataDictionary(Base):
    """数据字典表"""

    __tablename__ = "data_dictionaries"

    dict_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False
    )
    dict_type = Column(String(50), nullable=False, index=True, comment="字典类型")
    dict_label = Column(String(100), nullable=False, comment="字典标签（显示名）")
    dict_value = Column(String(255), nullable=False, comment="字典值（实际存储值）")
    sort_order = Column(Integer, default=0, comment="排序")
    is_active = Column(Integer, default=1, comment="是否启用")
    remark = Column(Text, nullable=True, comment="备注")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
