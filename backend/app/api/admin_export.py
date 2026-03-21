"""
管理 API - 导出字段模板配置
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.export_template import ExportTemplate, TemplateType
from app.middleware.auth import get_current_user, require_roles


router = APIRouter(prefix="/api/admin/export-templates", tags=["管理"])


class ExportTemplateOut(BaseModel):
    template_id: UUID
    template_type: str
    column_index: int
    xml_tag: Optional[str]
    display_name: str
    data_key: str
    is_active: bool

    class Config:
        from_attributes = True


class ExportTemplateUpdate(BaseModel):
    xml_tag: Optional[str] = None
    display_name: Optional[str] = None
    data_key: Optional[str] = None
    is_active: Optional[bool] = None


class ReorderRequest(BaseModel):
    template_type: str = Field(..., pattern="^(NDRC|MOFCOM)$")
    ordered_ids: list[UUID] = Field(..., description="按顺序排列的 template_id 列表")


@router.get("", response_model=list[ExportTemplateOut])
async def list_templates(
    template_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    """获取所有导出字段模板（可按类型过滤）"""
    query = select(ExportTemplate).order_by(
        ExportTemplate.template_type, ExportTemplate.column_index
    )
    if template_type:
        query = query.where(ExportTemplate.template_type == TemplateType(template_type))
    result = await db.execute(query)
    templates = result.scalars().all()
    return [
        ExportTemplateOut(
            template_id=t.template_id,
            template_type=t.template_type.value,
            column_index=t.column_index,
            xml_tag=t.xml_tag,
            display_name=t.display_name,
            data_key=t.data_key,
            is_active=t.is_active,
        )
        for t in templates
    ]


@router.put("/{template_type}/{template_id}", response_model=ExportTemplateOut)
async def update_template(
    template_type: str,
    template_id: UUID,
    data: ExportTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    """更新单个导出字段模板"""
    result = await db.execute(
        select(ExportTemplate).where(
            ExportTemplate.template_id == template_id,
            ExportTemplate.template_type == TemplateType(template_type),
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if data.xml_tag is not None:
        template.xml_tag = data.xml_tag
    if data.display_name is not None:
        template.display_name = data.display_name
    if data.data_key is not None:
        template.data_key = data.data_key
    if data.is_active is not None:
        template.is_active = data.is_active

    await db.flush()
    return ExportTemplateOut(
        template_id=template.template_id,
        template_type=template.template_type.value,
        column_index=template.column_index,
        xml_tag=template.xml_tag,
        display_name=template.display_name,
        data_key=template.data_key,
        is_active=template.is_active,
    )


@router.post("/reorder")
async def reorder_templates(
    data: ReorderRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    """批量重排模板字段顺序"""
    if len(data.ordered_ids) != len(set(data.ordered_ids)):
        raise HTTPException(status_code=400, detail="ordered_ids 包含重复 ID")

    result = await db.execute(
        select(ExportTemplate).where(
            ExportTemplate.template_type == TemplateType(data.template_type),
            ExportTemplate.template_id.in_(data.ordered_ids),
        )
    )
    templates = {t.template_id: t for t in result.scalars().all()}

    if len(templates) != len(data.ordered_ids):
        raise HTTPException(status_code=404, detail="部分模板 ID 不存在")

    for idx, tid in enumerate(data.ordered_ids):
        templates[tid].column_index = idx + 1

    await db.flush()
    return {"message": "排序已更新"}
