"""
境内外主体 API - CRUD
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.entity import EntityDomestic, EntityOverseas
from app.schemas.schemas import (
    EntityDomesticCreate, EntityDomesticOut, EntityDomesticUpdate,
    EntityOverseasCreate, EntityOverseasOut, EntityOverseasUpdate,
    MessageResponse,
)
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/entities", tags=["主体管理"])


# ==================== 境内主体 ====================

@router.post("/domestic", response_model=EntityDomesticOut)
async def create_domestic(
    data: EntityDomesticCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entity = EntityDomestic(
        tenant_id=current_user.tenant_id,
        **data.model_dump(),
    )
    db.add(entity)
    await db.flush()
    return entity


@router.get("/domestic", response_model=list[EntityDomesticOut])
async def list_domestic(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EntityDomestic)
        .where(EntityDomestic.tenant_id == current_user.tenant_id)
        .order_by(EntityDomestic.created_at.desc())
    )
    return result.scalars().all()


@router.get("/domestic/{entity_id}", response_model=EntityDomesticOut)
async def get_domestic(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EntityDomestic).where(
            EntityDomestic.entity_id == entity_id,
            EntityDomestic.tenant_id == current_user.tenant_id,
        )
    )
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="境内主体不存在")
    return entity


@router.put("/domestic/{entity_id}", response_model=EntityDomesticOut)
async def update_domestic(
    entity_id: UUID,
    data: EntityDomesticUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EntityDomestic).where(
            EntityDomestic.entity_id == entity_id,
            EntityDomestic.tenant_id == current_user.tenant_id,
        )
    )
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="境内主体不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(entity, key, value)
    await db.flush()
    return entity


@router.delete("/domestic/{entity_id}", response_model=MessageResponse)
async def delete_domestic(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EntityDomestic).where(
            EntityDomestic.entity_id == entity_id,
            EntityDomestic.tenant_id == current_user.tenant_id,
        )
    )
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="境内主体不存在")
    await db.delete(entity)
    return MessageResponse(message="已删除")


# ==================== 境外标的 ====================

@router.post("/overseas", response_model=EntityOverseasOut)
async def create_overseas(
    data: EntityOverseasCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entity = EntityOverseas(
        tenant_id=current_user.tenant_id,
        **data.model_dump(),
    )
    db.add(entity)
    await db.flush()
    return entity


@router.get("/overseas", response_model=list[EntityOverseasOut])
async def list_overseas(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EntityOverseas)
        .where(EntityOverseas.tenant_id == current_user.tenant_id)
        .order_by(EntityOverseas.created_at.desc())
    )
    return result.scalars().all()


@router.get("/overseas/{entity_id}", response_model=EntityOverseasOut)
async def get_overseas(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EntityOverseas).where(
            EntityOverseas.entity_id == entity_id,
            EntityOverseas.tenant_id == current_user.tenant_id,
        )
    )
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="境外标的不存在")
    return entity


@router.put("/overseas/{entity_id}", response_model=EntityOverseasOut)
async def update_overseas(
    entity_id: UUID,
    data: EntityOverseasUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EntityOverseas).where(
            EntityOverseas.entity_id == entity_id,
            EntityOverseas.tenant_id == current_user.tenant_id,
        )
    )
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="境外标的不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(entity, key, value)
    await db.flush()
    return entity


@router.delete("/overseas/{entity_id}", response_model=MessageResponse)
async def delete_overseas(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(EntityOverseas).where(
            EntityOverseas.entity_id == entity_id,
            EntityOverseas.tenant_id == current_user.tenant_id,
        )
    )
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="境外标的不存在")
    await db.delete(entity)
    return MessageResponse(message="已删除")
