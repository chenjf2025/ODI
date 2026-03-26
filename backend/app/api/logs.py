"""
系统日志 API - 操作日志/登录日志
"""

from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.system_log import SystemLog
from app.models.login_log import LoginLog
from app.schemas.schemas import SystemLogOut, LoginLogOut
from app.middleware.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/logs", tags=["系统日志"])


@router.get("/system", response_model=list[SystemLogOut])
async def list_system_logs(
    action: str = Query(None),
    resource: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    query = select(SystemLog).where(SystemLog.tenant_id == current_user.tenant_id)
    if action:
        query = query.where(SystemLog.action == action)
    if resource:
        query = query.where(SystemLog.resource == resource)
    query = query.order_by(SystemLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/login", response_model=list[LoginLogOut])
async def list_login_logs(
    login_status: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    query = select(LoginLog)
    if current_user.role != UserRole.ADMIN:
        query = query.where(LoginLog.tenant_id == current_user.tenant_id)
    if login_status:
        query = query.where(LoginLog.login_status == login_status)
    query = query.order_by(LoginLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    return result.scalars().all()
