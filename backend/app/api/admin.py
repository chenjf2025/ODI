"""
管理后台 API - LLM 配置 / 系统管理
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.llm_config import LLMConfig
from app.schemas.schemas import (
    LLMConfigCreate, LLMConfigOut, LLMConfigUpdate, MessageResponse
)
from app.middleware.auth import require_roles
from app.services.llm.gateway import llm_gateway

router = APIRouter(prefix="/api/admin", tags=["系统管理"])


async def _reload_providers():
    """热更新 LLM 提供商（从数据库重新加载）"""
    from app.main import reload_llm_providers_from_db
    # 清除旧注册
    llm_gateway._providers.clear()
    count = await reload_llm_providers_from_db()
    return count


@router.post("/llm-configs", response_model=LLMConfigOut)
async def create_llm_config(
    data: LLMConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    """添加 LLM 配置"""
    config = LLMConfig(**data.model_dump())
    db.add(config)
    await db.flush()
    await db.commit()
    await _reload_providers()
    return config


@router.get("/llm-configs", response_model=list[LLMConfigOut])
async def list_llm_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    """获取所有 LLM 配置"""
    result = await db.execute(
        select(LLMConfig).order_by(LLMConfig.priority)
    )
    return result.scalars().all()


@router.put("/llm-configs/{config_id}", response_model=LLMConfigOut)
async def update_llm_config(
    config_id: UUID,
    data: LLMConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    config = await db.get(LLMConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(config, key, value)
    await db.flush()
    await db.commit()
    await _reload_providers()
    return config


@router.delete("/llm-configs/{config_id}", response_model=MessageResponse)
async def delete_llm_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    config = await db.get(LLMConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    await db.delete(config)
    await db.commit()
    await _reload_providers()
    return MessageResponse(message="配置已删除")


@router.post("/llm-configs/reload", response_model=MessageResponse)
async def reload_llm_configs(
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    """手动重新加载所有 LLM 配置"""
    count = await _reload_providers()
    return MessageResponse(message=f"已重新加载 {count} 个 LLM 提供商")

