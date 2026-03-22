"""
项目管理 API - CRUD / 状态流转 / 文件上传
"""

from uuid import UUID
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.schemas.schemas import (
    ProjectCreate,
    ProjectOut,
    ProjectStatusUpdate,
    PageResponse,
    MessageResponse,
)
from app.middleware.auth import get_current_user, require_roles
from app.services.project_service import ProjectService
from app.services.billing_service import BillingService
from app.services.document_service import (
    review_documents_for_step,
    get_step_requirements,
)
from app.schemas.schemas import DocumentCreate, DocumentOut, StepDocumentsOut
from app.models.project_document import ProjectDocument

router = APIRouter(prefix="/api/projects", tags=["项目管理"])


@router.post("", response_model=ProjectOut)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建新 ODI 项目（触发计费拦截）"""
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    # 计费拦截
    await BillingService.check_and_deduct(
        db, tenant, action_description="创建新 ODI 项目"
    )

    project = await ProjectService.create_project(
        db, data, current_user.tenant_id, current_user.user_id
    )
    return project


@router.get("", response_model=PageResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取项目列表"""
    items, total = await ProjectService.list_projects(
        db, current_user.tenant_id, page, page_size, status
    )
    return PageResponse(
        items=[ProjectOut.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取项目详情"""
    project = await ProjectService.get_project(db, project_id, current_user.tenant_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.put("/{project_id}/status", response_model=ProjectOut)
async def update_status(
    project_id: UUID,
    data: ProjectStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.OPERATOR, UserRole.ADMIN])),
):
    project = await ProjectService.get_project(db, project_id, current_user.tenant_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    doc_review = await review_documents_for_step(db, project_id, data.target_status)
    if not doc_review.get("passed"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "DOCUMENTS_INCOMPLETE",
                "message": doc_review["message"],
                "missing": doc_review.get("missing", []),
                "review_result": doc_review.get("review_result"),
            },
        )

    try:
        project = await ProjectService.transition_status(
            db,
            project,
            data.target_status,
            current_user.user_id,
            data.remark,
            data.ndrc_certificate_url,
            data.mofcom_certificate_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return project


@router.get("/{project_id}/documents", response_model=List[StepDocumentsOut])
async def list_project_documents(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await ProjectService.get_project(db, project_id, current_user.tenant_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    from sqlalchemy import select

    result = await db.execute(
        select(ProjectDocument).where(ProjectDocument.project_id == project_id)
    )
    all_docs = result.scalars().all()

    step_names = {
        "DATA_COLLECTION": "材料准备",
        "NDRC_FILING_PENDING": "发改委备案",
        "NDRC_APPROVED": "发改委获批",
        "MOFCOM_FILING_PENDING": "商务部备案",
        "MOFCOM_APPROVED": "商务部获批",
        "BANK_REG_PENDING": "银行外汇登记",
        "FUNDS_REMITTED": "资金汇出",
        "POST_INVESTMENT": "投后管理",
    }

    steps = [
        "DATA_COLLECTION",
        "NDRC_FILING_PENDING",
        "NDRC_APPROVED",
        "MOFCOM_FILING_PENDING",
        "MOFCOM_APPROVED",
        "BANK_REG_PENDING",
        "FUNDS_REMITTED",
        "POST_INVESTMENT",
    ]

    result_list = []
    for step in steps:
        requirements = get_step_requirements(step)
        docs_for_step = [d for d in all_docs if d.step_status == step]
        result_list.append(
            StepDocumentsOut(
                step_status=step,
                step_name=step_names.get(step, step),
                requirements=requirements,
                documents=[DocumentOut.model_validate(d) for d in docs_for_step],
            )
        )
    return result_list


@router.post("/{project_id}/documents", response_model=DocumentOut)
async def upload_project_document(
    project_id: UUID,
    data: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await ProjectService.get_project(db, project_id, current_user.tenant_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    doc = ProjectDocument(
        project_id=project_id,
        step_status=data.step_status,
        document_type=data.document_type,
        document_name=data.document_name,
        file_url=data.file_url,
        file_size=data.file_size,
        remark=data.remark,
        uploaded_by=current_user.user_id,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return DocumentOut.model_validate(doc)


@router.delete("/{project_id}/documents/{document_id}", response_model=MessageResponse)
async def delete_project_document(
    project_id: UUID,
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await ProjectService.get_project(db, project_id, current_user.tenant_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    from sqlalchemy import select

    result = await db.execute(
        select(ProjectDocument).where(
            ProjectDocument.document_id == document_id,
            ProjectDocument.project_id == project_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    await db.delete(doc)
    await db.flush()
    return MessageResponse(message="文档已删除")


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    """删除项目（仅管理员）"""
    project = await ProjectService.get_project(db, project_id, current_user.tenant_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    await ProjectService.delete_project(db, project)
    return MessageResponse(message="项目已删除")
