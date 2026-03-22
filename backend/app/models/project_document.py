"""
项目文档模型 - 各状态节点所需文件
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ProjectDocument(Base):
    """项目文档"""

    __tablename__ = "project_documents"

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects_investment.project_id", ondelete="CASCADE"),
        nullable=False,
    )
    step_status = Column(String(50), nullable=False, comment="对应的状态节点")
    document_type = Column(String(100), nullable=False, comment="文档类型")
    document_name = Column(String(255), nullable=False, comment="文档名称")
    file_url = Column(String(500), nullable=False, comment="文件存储URL")
    file_size = Column(String(50), nullable=True, comment="文件大小")
    remark = Column(Text, nullable=True, comment="备注说明")
    review_result = Column(Text, nullable=True, comment="AI审核结果")
    review_status = Column(
        String(20), default="pending", comment="审核状态: pending/approved/rejected"
    )
    uploaded_by = Column(UUID(as_uuid=True), nullable=True, comment="上传人")
    created_at = Column(DateTime, default=datetime.now)

    project = relationship("ProjectInvestment")
