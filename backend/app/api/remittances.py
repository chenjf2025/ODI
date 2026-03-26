"""
付汇记录 API - CRUD + 凭证上传
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.remittance import RemittanceRecord
from app.schemas.schemas import (
    RemittanceRecordCreate,
    RemittanceRecordOut,
    RemittanceRecordUpdate,
    MessageResponse,
)
from app.middleware.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/remittances", tags=["付汇登记"])


@router.post("", response_model=RemittanceRecordOut)
async def create_remittance(
    data: RemittanceRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.project import ProjectInvestment
    from sqlalchemy import Numeric

    project = await db.get(ProjectInvestment, data.project_id)
    if not project or project.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="项目不存在")

    record = RemittanceRecord(
        project_id=data.project_id,
        tenant_id=current_user.tenant_id,
        remittance_amount=data.remittance_amount,
        currency=data.currency,
        receiver_account_name=data.receiver_account_name,
        receiver_bank_name=data.receiver_bank_name,
        receiver_account_no=data.receiver_account_no,
        remittance_date=data.remittance_date,
        voucher_url=data.voucher_url,
        registered_by=current_user.user_id,
    )
    db.add(record)
    await db.flush()
    return record


@router.get("", response_model=list[RemittanceRecordOut])
async def list_remittances(
    project_id: UUID = Query(None),
    status: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(RemittanceRecord).where(
        RemittanceRecord.tenant_id == current_user.tenant_id
    )
    if project_id:
        query = query.where(RemittanceRecord.project_id == project_id)
    if status:
        query = query.where(RemittanceRecord.status == status)
    query = query.order_by(RemittanceRecord.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{record_id}", response_model=RemittanceRecordOut)
async def get_remittance(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(RemittanceRecord).where(
            RemittanceRecord.record_id == record_id,
            RemittanceRecord.tenant_id == current_user.tenant_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="付汇记录不存在")
    return record


@router.put("/{record_id}", response_model=RemittanceRecordOut)
async def update_remittance(
    record_id: UUID,
    data: RemittanceRecordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.OPERATOR])),
):
    result = await db.execute(
        select(RemittanceRecord).where(
            RemittanceRecord.record_id == record_id,
            RemittanceRecord.tenant_id == current_user.tenant_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="付汇记录不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    await db.flush()
    return record


@router.delete("/{record_id}", response_model=MessageResponse)
async def delete_remittance(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    result = await db.execute(
        select(RemittanceRecord).where(
            RemittanceRecord.record_id == record_id,
            RemittanceRecord.tenant_id == current_user.tenant_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="付汇记录不存在")
    await db.delete(record)
    return MessageResponse(message="付汇记录已删除")
