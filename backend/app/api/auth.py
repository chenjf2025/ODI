"""
认证 API - 登录 / 注册 / Token 刷新
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.models.user import User, UserRole
from app.models.tenant import Tenant, SubscriptionPlan
from app.schemas.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.middleware.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_current_user,
)
from app.main import limiter

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=TokenResponse)
@limiter.limit("10/minute")
async def register(
    request: Request, data: RegisterRequest, db: AsyncSession = Depends(get_db)
):
    """用户注册（同时创建租户）"""
    existing = await db.execute(
        select(User).where(
            (User.username == data.username) | (User.email == data.email)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在")

    tenant = Tenant(
        agency_name=data.agency_name or f"{data.username}的机构",
        subscription_plan=SubscriptionPlan.FREE,
        balance_credits=5,
    )
    db.add(tenant)
    await db.flush()

    user = User(
        tenant_id=tenant.tenant_id,
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole.ADMIN,
    )
    db.add(user)
    await db.flush()

    token = create_access_token({"sub": str(user.user_id)})
    refresh_token = create_refresh_token({"sub": str(user.user_id)})
    return TokenResponse(
        access_token=token,
        refresh_token=refresh_token,
        user_id=str(user.user_id),
        role=user.role.value if hasattr(user.role, "value") else user.role,
        tenant_id=str(tenant.tenant_id),
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("20/minute")
async def login(
    request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已被禁用")

    token = create_access_token({"sub": str(user.user_id)})
    refresh_token = create_refresh_token({"sub": str(user.user_id)})
    return TokenResponse(
        access_token=token,
        refresh_token=refresh_token,
        user_id=str(user.user_id),
        role=user.role.value if hasattr(user.role, "value") else user.role,
        tenant_id=str(user.tenant_id),
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
async def refresh_token(request: Request, db: AsyncSession = Depends(get_db)):
    """使用 refresh token 刷新 access token"""
    from fastapi import Header
    from jose import jwt, JWTError
    from app.config import settings

    refresh = request.headers.get("X-Refresh-Token", "")
    if not refresh:
        raise HTTPException(status_code=401, detail="缺少 refresh token")

    try:
        payload = jwt.decode(
            refresh, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的 refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="refresh token 已失效或伪造")

    result = await db.execute(select(User).where(User.user_id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")

    token = create_access_token({"sub": str(user.user_id)})
    new_refresh = create_refresh_token({"sub": str(user.user_id)})
    return TokenResponse(
        access_token=token,
        refresh_token=new_refresh,
        user_id=str(user.user_id),
        role=user.role.value if hasattr(user.role, "value") else user.role,
        tenant_id=str(user.tenant_id),
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user
