from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.sensitive_word import SensitiveWord, SensitiveLevel
from app.schemas.schemas import (
    SensitiveWordCreate,
    SensitiveWordOut,
    SensitiveWordUpdate,
    MessageResponse,
)
from app.middleware.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/sensitive-words", tags=["敏感词管理"])


@router.get("", response_model=list[SensitiveWordOut])
async def list_sensitive_words(
    level: Optional[str] = Query(None),
    is_active: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(SensitiveWord).where(
        SensitiveWord.tenant_id == current_user.tenant_id
    )
    if level:
        query = query.where(SensitiveWord.level == level)
    if is_active is not None:
        query = query.where(SensitiveWord.is_active == is_active)
    query = query.order_by(SensitiveWord.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=SensitiveWordOut)
async def create_sensitive_word(
    data: SensitiveWordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    word = SensitiveWord(
        tenant_id=current_user.tenant_id,
        **data.model_dump(),
    )
    db.add(word)
    await db.flush()
    return word


@router.put("/{word_id}", response_model=SensitiveWordOut)
async def update_sensitive_word(
    word_id: UUID,
    data: SensitiveWordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    result = await db.execute(
        select(SensitiveWord).where(
            SensitiveWord.word_id == word_id,
            SensitiveWord.tenant_id == current_user.tenant_id,
        )
    )
    word = result.scalar_one_or_none()
    if not word:
        raise HTTPException(status_code=404, detail="敏感词不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(word, key, value)
    await db.flush()
    return word


@router.delete("/{word_id}", response_model=MessageResponse)
async def delete_sensitive_word(
    word_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    result = await db.execute(
        select(SensitiveWord).where(
            SensitiveWord.word_id == word_id,
            SensitiveWord.tenant_id == current_user.tenant_id,
        )
    )
    word = result.scalar_one_or_none()
    if not word:
        raise HTTPException(status_code=404, detail="敏感词不存在")
    await db.delete(word)
    return MessageResponse(message="敏感词已删除")
