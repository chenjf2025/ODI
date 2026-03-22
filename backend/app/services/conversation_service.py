"""
对话历史服务 - 存储和查询会话历史，生成跟进建议
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.models.conversation import (
    ConversationSession,
    ConversationMessage,
    ConversationFeedback,
)


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self, tenant_id: UUID, user_id: UUID, first_message: Optional[str] = None
    ) -> ConversationSession:
        title = (first_message or "新对话")[:80]
        session = ConversationSession(
            tenant_id=tenant_id,
            user_id=user_id,
            title=title,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def add_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        intent: Optional[str] = None,
        confidence: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> ConversationMessage:
        msg = ConversationMessage(
            session_id=session_id,
            role=role,
            content=content,
            intent=intent,
            confidence=confidence,
            metadata_=metadata,
        )
        self.db.add(msg)
        await self.db.flush()
        return msg

    async def get_sessions(
        self, tenant_id: UUID, user_id: UUID, limit: int = 50
    ) -> List[ConversationSession]:
        result = await self.db.execute(
            select(ConversationSession)
            .where(
                ConversationSession.tenant_id == tenant_id,
                ConversationSession.user_id == user_id,
                ConversationSession.is_deleted == 0,
            )
            .order_by(desc(ConversationSession.updated_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_session_with_messages(
        self, session_id: UUID, tenant_id: UUID
    ) -> Optional[ConversationSession]:
        result = await self.db.execute(
            select(ConversationSession).where(
                ConversationSession.session_id == session_id,
                ConversationSession.tenant_id == tenant_id,
                ConversationSession.is_deleted == 0,
            )
        )
        return result.scalars().first()

    async def update_session_title(self, session_id: UUID, title: str):
        result = await self.db.execute(
            select(ConversationSession).where(
                ConversationSession.session_id == session_id
            )
        )
        session = result.scalars().first()
        if session:
            session.title = title
            await self.db.flush()

    async def delete_session(self, session_id: UUID, tenant_id: UUID):
        result = await self.db.execute(
            select(ConversationSession).where(
                ConversationSession.session_id == session_id,
                ConversationSession.tenant_id == tenant_id,
            )
        )
        session = result.scalars().first()
        if session:
            session.is_deleted = 1
            await self.db.flush()

    async def submit_feedback(
        self,
        session_id: UUID,
        user_id: UUID,
        rating: str,
        comment: Optional[str] = None,
    ) -> ConversationFeedback:
        fb = ConversationFeedback(
            session_id=session_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
        )
        self.db.add(fb)
        await self.db.flush()
        return fb

    def generate_suggestions(self, intent: str, last_user_message: str) -> List[str]:
        suggestions_map = {
            "create_project": [
                "帮我查询这个项目的详细信息",
                "对这个项目进行智能预审",
                "生成一份可行性研究报告",
            ],
            "query_project": [
                "对这个项目做预审分析",
                "导出发改委备案文件",
                "生成项目报告",
            ],
            "pre_review": [
                "查看完整的预审报告详情",
                "对这个项目生成尽调报告",
                "推进项目到下一阶段",
            ],
            "generate_report": [
                "把这个报告导出为PDF",
                "对这个项目进行预审",
                "导出发改委备案文件",
            ],
            "export_ndrc": [
                "同时导出一份商务部Excel",
                "对这个项目进行智能预审",
                "查看项目当前状态",
            ],
            "export_mofcom": [
                "导出发改委XML文件",
                "查看项目预审结果",
                "继续下一步流程",
            ],
            "query_entity": [
                "创建一个使用这个主体的项目",
                "查询这个主体的项目情况",
                "添加更多主体信息",
            ],
            "query_rules": [
                "查询高风险国家的投资规定",
                "哪些行业需要特别审批",
                "创建一个涉及高风险行业的项目",
            ],
            "knowledge_qa": [
                "可以详细说说ODI备案流程吗",
                "发改委和商务部的区别是什么",
                "我需要准备哪些材料",
            ],
            "general_chat": [
                "帮我创建一个去新加坡投资的项目",
                "介绍一下ODI备案的基本流程",
                "查询一下我现有的项目",
            ],
        }
        return suggestions_map.get(intent, suggestions_map["general_chat"])
