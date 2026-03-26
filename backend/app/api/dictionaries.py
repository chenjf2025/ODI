"""
数据字典 API - 类型管理 + 值管理
"""

from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.data_dictionary import DataDictionary
from app.schemas.schemas import (
    DataDictionaryCreate,
    DataDictionaryOut,
    DataDictionaryUpdate,
    DataDictionaryTypeOut,
    MessageResponse,
)
from app.middleware.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/dictionaries", tags=["数据字典"])


@router.get("/types", response_model=list[DataDictionaryTypeOut])
async def list_dict_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(distinct(DataDictionary.dict_type)).where(
            DataDictionary.tenant_id == current_user.tenant_id
        )
    )
    types = result.scalars().all()
    return [{"dict_type": t} for t in types]


@router.post("", response_model=DataDictionaryOut)
async def create_dict(
    data: DataDictionaryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    dic = DataDictionary(
        tenant_id=current_user.tenant_id,
        **data.model_dump(),
    )
    db.add(dic)
    await db.flush()
    return dic


@router.get("", response_model=list[DataDictionaryOut])
async def list_dicts(
    dict_type: Optional[str] = Query(None),
    is_active: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(DataDictionary).where(
        DataDictionary.tenant_id == current_user.tenant_id
    )
    if dict_type:
        query = query.where(DataDictionary.dict_type == dict_type)
    if is_active is not None:
        query = query.where(DataDictionary.is_active == is_active)
    query = query.order_by(DataDictionary.sort_order)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{dict_id}", response_model=DataDictionaryOut)
async def get_dict(
    dict_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(DataDictionary).where(
            DataDictionary.dict_id == dict_id,
            DataDictionary.tenant_id == current_user.tenant_id,
        )
    )
    dic = result.scalar_one_or_none()
    if not dic:
        raise HTTPException(status_code=404, detail="字典不存在")
    return dic


@router.put("/{dict_id}", response_model=DataDictionaryOut)
async def update_dict(
    dict_id: UUID,
    data: DataDictionaryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    result = await db.execute(
        select(DataDictionary).where(
            DataDictionary.dict_id == dict_id,
            DataDictionary.tenant_id == current_user.tenant_id,
        )
    )
    dic = result.scalar_one_or_none()
    if not dic:
        raise HTTPException(status_code=404, detail="字典不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(dic, key, value)
    await db.flush()
    return dic


@router.delete("/{dict_id}", response_model=MessageResponse)
async def delete_dict(
    dict_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    result = await db.execute(
        select(DataDictionary).where(
            DataDictionary.dict_id == dict_id,
            DataDictionary.tenant_id == current_user.tenant_id,
        )
    )
    dic = result.scalar_one_or_none()
    if not dic:
        raise HTTPException(status_code=404, detail="字典不存在")
    await db.delete(dic)
    return MessageResponse(message="字典已删除")
