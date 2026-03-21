"""
AI 服务 API - 预审 / 报告生成 / 财务数据抽取
"""

from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
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
)
from app.middleware.auth import get_current_user, require_roles
from app.services.project_service import ProjectService
from app.services.billing_service import BillingService
from app.services.ai_service import ai_service
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
        # 这里简化处理，实际应读取上传的文件内容
        result = await ai_service.extract_financial_data(
            f"请提取项目 {data.project_id} 关联的财务数据（来自文件 {data.file_url}）"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据抽取失败: {str(e)}")

    return {
        "project_id": str(data.project_id),
        "extracted_data": result,
    }
