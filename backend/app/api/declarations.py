"""
对外申报记录 API - 材料归集/申报/Mock状态
"""

from uuid import UUID
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.declaration import (
    DeclarationRecord,
    DeclarationStatus,
    DeclarationTarget,
)
from app.schemas.schemas import (
    DeclarationRecordCreate,
    DeclarationRecordOut,
    DeclarationUpdate,
    MessageResponse,
)
from app.middleware.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/declarations", tags=["对外申报"])


@router.post("", response_model=DeclarationRecordOut)
async def create_declaration(
    data: DeclarationRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.project import ProjectInvestment

    project = await db.get(ProjectInvestment, data.project_id)
    if not project or project.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="项目不存在")

    record = DeclarationRecord(
        project_id=data.project_id,
        tenant_id=current_user.tenant_id,
        target=DeclarationTarget[data.target.upper()],
        status=DeclarationStatus.PENDING,
        submitted_by=current_user.user_id,
        remark=data.remark,
    )
    db.add(record)
    await db.flush()
    return record


@router.get("", response_model=list[DeclarationRecordOut])
async def list_declarations(
    project_id: UUID = Query(None),
    status: str = Query(None),
    target: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(DeclarationRecord).where(
        DeclarationRecord.tenant_id == current_user.tenant_id
    )
    if project_id:
        query = query.where(DeclarationRecord.project_id == project_id)
    if status:
        query = query.where(DeclarationRecord.status == status)
    if target:
        query = query.where(
            DeclarationRecord.target == DeclarationTarget[target.upper()]
        )
    query = query.order_by(DeclarationRecord.created_at.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{record_id}", response_model=DeclarationRecordOut)
async def get_declaration(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(DeclarationRecord).where(
            DeclarationRecord.record_id == record_id,
            DeclarationRecord.tenant_id == current_user.tenant_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="申报记录不存在")
    return record


@router.post("/{record_id}/submit", response_model=DeclarationRecordOut)
async def submit_declaration(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = await db.get(DeclarationRecord, record_id)
    if not record or record.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="申报记录不存在")

    if record.status != DeclarationStatus.PENDING:
        raise HTTPException(status_code=400, detail="当前状态不允许提交")

    record.status = DeclarationStatus.IN_PROGRESS
    record.submitted_at = datetime.now()

    receipt_no = f"MOCK-{uuid.uuid4().hex[:12].upper()}"
    record.receipt_no = receipt_no
    record.receipt_data = {
        "receipt_no": receipt_no,
        "submit_time": datetime.now().isoformat(),
        "target": record.target.value,
        "mock_mode": True,
        "message": "Mock模式：申报已提交，7个工作日内完成审核",
    }

    await db.flush()
    return record


@router.post("/{record_id}/approve", response_model=DeclarationRecordOut)
async def approve_declaration(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    record = await db.get(DeclarationRecord, record_id)
    if not record or record.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="申报记录不存在")

    if record.status != DeclarationStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="当前状态不允许审核")

    record.status = DeclarationStatus.APPROVED
    if record.receipt_data:
        record.receipt_data["approve_time"] = datetime.now().isoformat()
        record.receipt_data["approved_by"] = str(current_user.user_id)

    await db.flush()
    return record


@router.post("/{record_id}/reject", response_model=DeclarationRecordOut)
async def reject_declaration(
    record_id: UUID,
    data: DeclarationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    record = await db.get(DeclarationRecord, record_id)
    if not record or record.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="申报记录不存在")

    if record.status != DeclarationStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="当前状态不允许驳回")

    record.status = DeclarationStatus.REJECTED
    if data.remark:
        record.remark = data.remark

    await db.flush()
    return record


@router.put("/{record_id}", response_model=DeclarationRecordOut)
async def update_declaration(
    record_id: UUID,
    data: DeclarationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = await db.get(DeclarationRecord, record_id)
    if not record or record.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="申报记录不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    await db.flush()
    return record
