"""
规则引擎 API - CRUD（Admin 权限）
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.rules import RulesEngine
from app.schemas.schemas import RuleCreate, RuleOut, RuleUpdate, MessageResponse
from app.middleware.auth import get_current_user, require_roles
from app.services.rules_service import RulesService

router = APIRouter(prefix="/api/rules", tags=["规则引擎"])


@router.post("", response_model=RuleOut)
async def create_rule(
    data: RuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    """创建合规规则"""
    rule = RulesEngine(**data.model_dump())
    db.add(rule)
    await db.flush()
    return rule


@router.get("", response_model=list[RuleOut])
async def list_rules(
    rule_type: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取规则列表"""
    rules = await RulesService.get_all_rules(db, rule_type)
    return rules


@router.get("/{rule_id}", response_model=RuleOut)
async def get_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rule = await db.get(RulesEngine, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    return rule


@router.put("/{rule_id}", response_model=RuleOut)
async def update_rule(
    rule_id: UUID,
    data: RuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    rule = await db.get(RulesEngine, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    await db.flush()
    return rule


@router.delete("/{rule_id}", response_model=MessageResponse)
async def delete_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    rule = await db.get(RulesEngine, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    await db.delete(rule)
    return MessageResponse(message="规则已删除")
