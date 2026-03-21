"""
租户管理与计费 API
"""
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.models.billing import BillingLog
from app.schemas.schemas import (
    TenantOut, TenantUpdate, CreditTopup,
    BillingLogOut, MessageResponse
)
from app.middleware.auth import get_current_user, require_roles
from app.services.billing_service import BillingService

router = APIRouter(prefix="/api/tenants", tags=["租户管理"])


@router.get("/current", response_model=TenantOut)
async def get_current_tenant(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前租户信息"""
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    return tenant


@router.put("/current", response_model=TenantOut)
async def update_tenant(
    data: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    """更新租户信息"""
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(tenant, key, value)
    await db.flush()
    return tenant


@router.post("/topup", response_model=TenantOut)
async def topup_credits(
    data: CreditTopup,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    """充值点数"""
    tenant = await db.get(Tenant, current_user.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    tenant = await BillingService.topup_credits(db, tenant, data.credits, data.remark or "点数充值")
    return tenant


@router.get("/billing-logs", response_model=list[BillingLogOut])
async def list_billing_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """计费流水查询"""
    result = await db.execute(
        select(BillingLog)
        .where(BillingLog.tenant_id == current_user.tenant_id)
        .order_by(BillingLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return result.scalars().all()
