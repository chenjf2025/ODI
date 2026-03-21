"""
项目管理 API - CRUD / 状态流转 / 文件上传
"""
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.schemas.schemas import (
    ProjectCreate, ProjectOut, ProjectStatusUpdate,
    PageResponse, MessageResponse
)
from app.middleware.auth import get_current_user, require_roles
from app.services.project_service import ProjectService
from app.services.billing_service import BillingService

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
    current_user: User = Depends(
        require_roles([UserRole.OPERATOR, UserRole.ADMIN])
    ),
):
    """推进项目状态（仅运营/管理员）"""
    project = await ProjectService.get_project(db, project_id, current_user.tenant_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    try:
        project = await ProjectService.transition_status(
            db, project, data.target_status, current_user.user_id, data.remark,
            data.ndrc_certificate_url, data.mofcom_certificate_url
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return project


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.ADMIN])
    ),
):
    """删除项目（仅管理员）"""
    project = await ProjectService.get_project(db, project_id, current_user.tenant_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    await ProjectService.delete_project(db, project)
    return MessageResponse(message="项目已删除")
