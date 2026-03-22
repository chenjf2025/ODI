"""
AI 服务 API - 预审 / 报告生成 / 财务数据抽取 / 对话历史
"""

from uuid import UUID
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.schemas.schemas import (
    PreReviewRequest,
    PreReviewResponse,
    ReportGenerateRequest,
    ReportGenerateResponse,
    FinancialExtractRequest,
    FinancialExtractResponse,
    ChatRequest,
    ChatResponse,
)
from app.middleware.auth import get_current_user, require_roles
from app.services.project_service import ProjectService
from app.services.billing_service import BillingService
from app.services.ai_service import ai_service
from app.services.conversation_service import ConversationService
from app.utils import utc_now

router = APIRouter(prefix="/api/ai", tags=["AI 服务"])


@router.post("/pre-review", response_model=PreReviewResponse)
async def pre_review(
    data: PreReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """智能预审"""
    project = await ProjectService.get_project(
        db, data.project_id, current_user.tenant_id
    )
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    try:
        report = await ai_service.pre_review(db, project)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预审失败: {str(e)}")

    actual_usage = ai_service.last_llm_usage
    await BillingService.check_and_deduct(
        db, tenant, project.project_id, "AI 智能预审", usage=actual_usage
    )

    return PreReviewResponse(
        project_id=project.project_id,
        risk_level=report.get("risk_level", ""),
        traffic_light=report.get("traffic_light", "GREEN"),
        summary=report.get("ai_analysis", ""),
        matched_rules=report.get("matched_rules", []),
        recommendations=report.get("recommendations", []),
    )


@router.post("/generate-report", response_model=ReportGenerateResponse)
async def generate_report(
    data: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OPERATOR, UserRole.ADMIN])),
):
    """生成可研报告 / 尽调报告"""
    project = await ProjectService.get_project(
        db, data.project_id, current_user.tenant_id
    )
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    try:
        if data.report_type == "feasibility":
            content = await ai_service.generate_feasibility_report(db, project)
        elif data.report_type == "due_diligence":
            content = await ai_service.generate_due_diligence_report(db, project)
        else:
            raise HTTPException(
                status_code=400,
                detail="不支持的报告类型，可选: feasibility, due_diligence",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")

    actual_usage = ai_service.last_llm_usage
    await BillingService.check_and_deduct(
        db,
        tenant,
        project.project_id,
        f"AI 生成{data.report_type}报告",
        usage=actual_usage,
    )

    return ReportGenerateResponse(
        project_id=project.project_id,
        report_type=data.report_type,
        content=content,
        generated_at=utc_now(),
    )


@router.post("/extract-financial")
async def extract_financial(
    data: FinancialExtractRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从审计报告中抽取财务数据"""
    try:
        result = await ai_service.extract_financial_data(
            f"请提取项目 {data.project_id} 关联的财务数据（来自文件 {data.file_url}）"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据抽取失败: {str(e)}")

    return {
        "project_id": str(data.project_id),
        "extracted_data": result,
    }


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """统一 AI 对话入口 — 意图分类 + 动作执行 + LLM 回复"""
    import logging

    logger = logging.getLogger(__name__)

    from app.services.ai_service import chat
    from app.services.conversation_service import ConversationService

    try:
        conv_service = ConversationService(db)
        session_id = UUID(data.session_id) if data.session_id else None

        if session_id:
            session = await conv_service.get_session_with_messages(
                session_id, current_user.tenant_id
            )
            if not session:
                raise HTTPException(status_code=404, detail="会话不存在")
        else:
            first_msg = data.messages[0].content if data.messages else "新对话"
            session = await conv_service.create_session(
                tenant_id=current_user.tenant_id,
                user_id=current_user.user_id,
                first_message=first_msg,
            )

        for m in data.messages:
            await conv_service.add_message(
                session_id=session.session_id,
                role=m.role,
                content=m.content,
            )

        result = await chat(
            db=db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id,
            messages=[m.model_dump() for m in data.messages],
            attachments=[a.model_dump() for a in data.attachments]
            if data.attachments
            else None,
            context_project_id=data.context_project_id,
            session_id=session.session_id,
        )

        last_user_msg = next(
            (m.content for m in reversed(data.messages) if m.role == "user"), ""
        )
        await conv_service.add_message(
            session_id=session.session_id,
            role="assistant",
            content=result.get("content") or "",
            intent=result.get("intent"),
            confidence=str(result.get("confidence", ""))
            if result.get("confidence") is not None
            else None,
        )

        suggestions = conv_service.generate_suggestions(
            result.get("intent", "general_chat"), last_user_msg
        )

        response_data = ChatResponse(
            content=result.get("content") or "",
            intent=result.get("intent") or "general_chat",
            confidence=float(result.get("confidence", 0.0))
            if result.get("confidence") is not None
            else 0.0,
            actions=result.get("actions") or [],
            usage=result.get("usage"),
            session_id=str(session.session_id),
            suggestions=suggestions,
        )
        await db.commit()
        return response_data
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("chat_endpoint error: %s", e)
        import traceback

        logger.exception("Traceback: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"chat_endpoint error: {e}")


class ConversationListOut(BaseModel):
    session_id: str
    title: Optional[str] = None
    updated_at: datetime
    message_count: int = 0


class MessageOut(BaseModel):
    message_id: str
    role: str
    content: str
    intent: Optional[str] = None
    created_at: datetime


class ConversationDetailOut(BaseModel):
    session_id: str
    title: Optional[str] = None
    updated_at: datetime
    messages: List[MessageOut] = []


@router.get("/conversations", response_model=List[ConversationListOut])
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取会话列表"""
    conv_service = ConversationService(db)
    sessions = await conv_service.get_sessions(
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
    )
    return [
        ConversationListOut(
            session_id=str(s.session_id),
            title=s.title,
            updated_at=s.updated_at or s.created_at,
            message_count=len(s.messages) if s.messages else 0,
        )
        for s in sessions
    ]


@router.get("/conversations/{session_id}", response_model=ConversationDetailOut)
async def get_conversation(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取会话详情（含完整消息）"""
    conv_service = ConversationService(db)
    session = await conv_service.get_session_with_messages(
        session_id=session_id,
        tenant_id=current_user.tenant_id,
    )
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    return ConversationDetailOut(
        session_id=str(session.session_id),
        title=session.title,
        updated_at=session.updated_at or session.created_at,
        messages=[
            MessageOut(
                message_id=str(m.message_id),
                role=m.role,
                content=m.content,
                intent=m.intent,
                created_at=m.created_at,
            )
            for m in (session.messages or [])
        ],
    )


class FeedbackRequest(BaseModel):
    rating: str = Field(..., pattern="^(like|dislike)$")
    comment: Optional[str] = None


@router.post("/conversations/{session_id}/feedback")
async def submit_feedback(
    session_id: UUID,
    data: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交对话反馈（点赞/点踩）"""
    conv_service = ConversationService(db)
    session = await conv_service.get_session_with_messages(
        session_id, current_user.tenant_id
    )
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    await conv_service.submit_feedback(
        session_id=session_id,
        user_id=current_user.user_id,
        rating=data.rating,
        comment=data.comment,
    )
    await db.commit()
    return {"message": "反馈已提交，谢谢！"}


@router.delete("/conversations/{session_id}")
async def delete_conversation(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除会话（软删除）"""
    conv_service = ConversationService(db)
    await conv_service.delete_session(
        session_id=session_id,
        tenant_id=current_user.tenant_id,
    )
    await db.commit()
    return {"message": "会话已删除"}
