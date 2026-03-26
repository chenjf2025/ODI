"""
部门管理 API - CRUD + 树形结构
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.department import Department
from app.schemas.schemas import (
    DepartmentCreate,
    DepartmentOut,
    DepartmentUpdate,
    MessageResponse,
)
from app.middleware.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/departments", tags=["部门管理"])


def build_tree(depts: list[Department], parent_id: UUID = None) -> list[dict]:
    result = []
    for d in depts:
        if d.parent_id == parent_id:
            children = build_tree(depts, d.department_id)
            item = {
                "department_id": str(d.department_id),
                "department_name": d.department_name,
                "parent_id": str(d.parent_id) if d.parent_id else None,
                "sort_order": d.sort_order,
                "is_active": d.is_active,
                "children": children,
            }
            result.append(item)
    return result


@router.post("", response_model=DepartmentOut)
async def create_department(
    data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    dept = Department(
        tenant_id=current_user.tenant_id,
        parent_id=data.parent_id,
        department_name=data.department_name,
        leader_user_id=data.leader_user_id,
        sort_order=data.sort_order,
    )
    db.add(dept)
    await db.flush()
    return dept


@router.get("", response_model=list)
async def list_departments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Department)
        .where(Department.tenant_id == current_user.tenant_id)
        .order_by(Department.sort_order)
    )
    depts = result.scalars().all()
    return build_tree(list(depts))


@router.get("/flat", response_model=list[DepartmentOut])
async def list_departments_flat(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Department)
        .where(Department.tenant_id == current_user.tenant_id)
        .order_by(Department.sort_order)
    )
    return result.scalars().all()


@router.get("/{department_id}", response_model=DepartmentOut)
async def get_department(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Department).where(
            Department.department_id == department_id,
            Department.tenant_id == current_user.tenant_id,
        )
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")
    return dept


@router.put("/{department_id}", response_model=DepartmentOut)
async def update_department(
    department_id: UUID,
    data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    result = await db.execute(
        select(Department).where(
            Department.department_id == department_id,
            Department.tenant_id == current_user.tenant_id,
        )
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(dept, key, value)
    await db.flush()
    return dept


@router.delete("/{department_id}", response_model=MessageResponse)
async def delete_department(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    result = await db.execute(
        select(Department).where(
            Department.department_id == department_id,
            Department.tenant_id == current_user.tenant_id,
        )
    )
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")
    await db.delete(dept)
    return MessageResponse(message="部门已删除")
