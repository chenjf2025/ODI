"""
AI 对话历史模型 - 支持会话持久化和反馈
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(
        UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    title = Column(
        String(255), nullable=True, comment="会话标题，自动从首条用户消息截取"
    )
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = Column(Integer, default=0, comment="软删除标记")

    messages = relationship(
        "ConversationMessage", back_populates="session", lazy="selectin"
    )
    feedbacks = relationship(
        "ConversationFeedback", back_populates="session", lazy="selectin"
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversation_sessions.session_id"),
        nullable=False,
    )
    role = Column(String(20), nullable=False, comment="user / assistant / system")
    content = Column(Text, nullable=False)
    intent = Column(String(50), nullable=True, comment="该消息对应的AI意图类型")
    confidence = Column(String(10), nullable=True)
    metadata_ = Column(
        "metadata", JSON, nullable=True, comment="附加信息（attachments等）"
    )
    created_at = Column(DateTime, default=datetime.now)

    session = relationship("ConversationSession", back_populates="messages")


class ConversationFeedback(Base):
    __tablename__ = "conversation_feedbacks"

    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversation_sessions.session_id"),
        nullable=False,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    rating = Column(String(10), nullable=False, comment="like / dislike")
    comment = Column(Text, nullable=True, comment="用户可选留言")
    created_at = Column(DateTime, default=datetime.now)

    session = relationship("ConversationSession", back_populates="feedbacks")
