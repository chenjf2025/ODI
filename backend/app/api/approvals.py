"""
审批流程 API - 发起/审批/待办/已办
"""

from uuid import UUID
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.approval import ApprovalFlow, ApprovalLog, ApprovalStatus, ApprovalLevel
from app.schemas.schemas import (
    ApprovalFlowCreate,
    ApprovalFlowOut,
    ApprovalLogCreate,
    ApprovalLogOut,
    ApprovalDetailOut,
    MessageResponse,
)
from app.middleware.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/approvals", tags=["审批流程"])


@router.post("/flows", response_model=ApprovalFlowOut)
async def create_approval_flow(
    data: ApprovalFlowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.project import ProjectInvestment

    project = await db.get(ProjectInvestment, data.project_id)
    if not project or project.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="项目不存在")

    flow = ApprovalFlow(
        project_id=data.project_id,
        tenant_id=current_user.tenant_id,
        created_by=current_user.user_id,
        current_level=ApprovalLevel.FIRST,
        status=ApprovalStatus.PENDING,
    )
    db.add(flow)
    await db.flush()
    return flow


@router.get("/flows", response_model=list[ApprovalFlowOut])
async def list_approval_flows(
    project_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(ApprovalFlow).where(ApprovalFlow.tenant_id == current_user.tenant_id)
    if project_id:
        query = query.where(ApprovalFlow.project_id == project_id)
    if status:
        query = query.where(ApprovalFlow.status == status)
    query = query.order_by(ApprovalFlow.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/flows/pending", response_model=list[ApprovalFlowOut])
async def list_pending_approvals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(ApprovalFlow)
        .where(
            ApprovalFlow.tenant_id == current_user.tenant_id,
            ApprovalFlow.status == ApprovalStatus.PENDING,
            or_(
                ApprovalFlow.current_level == ApprovalLevel.FIRST,
                ApprovalFlow.current_level == ApprovalLevel.REVIEW,
                ApprovalFlow.current_level == ApprovalLevel.FINAL,
            ),
        )
        .order_by(ApprovalFlow.created_at.desc())
    )

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/flows/{flow_id}", response_model=ApprovalDetailOut)
async def get_approval_flow(
    flow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    flow = await db.get(ApprovalFlow, flow_id)
    if not flow or flow.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="审批流程不存在")

    result = await db.execute(
        select(ApprovalLog)
        .where(ApprovalLog.flow_id == flow_id)
        .order_by(ApprovalLog.created_at)
    )
    logs = result.scalars().all()

    return ApprovalDetailOut(
        flow=ApprovalFlowOut.model_validate(flow),
        logs=[ApprovalLogOut.model_validate(log) for log in logs],
    )


@router.post("/flows/{flow_id}/approve", response_model=ApprovalFlowOut)
async def approve_flow(
    flow_id: UUID,
    data: ApprovalLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request=None,
):
    flow = await db.get(ApprovalFlow, flow_id)
    if not flow or flow.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="审批流程不存在")

    if flow.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail="当前状态不允许审批")

    ip_address = None
    if request:
        ip_address = request.client.host if request.client else None

    log = ApprovalLog(
        flow_id=flow_id,
        approver_id=current_user.user_id,
        level=flow.current_level,
        action=ApprovalStatus.APPROVED,
        opinion=data.opinion,
        operator_ip=ip_address,
    )
    db.add(log)

    if flow.current_level == ApprovalLevel.FINAL:
        flow.status = ApprovalStatus.APPROVED
        flow.completed_at = datetime.now()
        flow.completed_by = current_user.user_id
    elif flow.current_level == ApprovalLevel.FIRST:
        flow.current_level = ApprovalLevel.REVIEW
    elif flow.current_level == ApprovalLevel.REVIEW:
        flow.current_level = ApprovalLevel.FINAL

    await db.flush()
    return flow


@router.post("/flows/{flow_id}/reject", response_model=ApprovalFlowOut)
async def reject_flow(
    flow_id: UUID,
    data: ApprovalLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request=None,
):
    flow = await db.get(ApprovalFlow, flow_id)
    if not flow or flow.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="审批流程不存在")

    if flow.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail="当前状态不允许审批")

    ip_address = None
    if request:
        ip_address = request.client.host if request.client else None

    log = ApprovalLog(
        flow_id=flow_id,
        approver_id=current_user.user_id,
        level=flow.current_level,
        action=ApprovalStatus.REJECTED,
        opinion=data.opinion,
        operator_ip=ip_address,
    )
    db.add(log)

    flow.status = ApprovalStatus.REJECTED
    flow.completed_at = datetime.now()
    flow.completed_by = current_user.user_id

    await db.flush()
    return flow


@router.post("/flows/{flow_id}/withdraw", response_model=ApprovalFlowOut)
async def withdraw_flow(
    flow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    flow = await db.get(ApprovalFlow, flow_id)
    if not flow or flow.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="审批流程不存在")

    if flow.created_by != current_user.user_id:
        raise HTTPException(status_code=403, detail="只有申请人可以撤回")

    if flow.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail="当前状态不允许撤回")

    flow.status = ApprovalStatus.WITHDRAWN
    flow.completed_at = datetime.now()
    flow.completed_by = current_user.user_id

    await db.flush()
    return flow
