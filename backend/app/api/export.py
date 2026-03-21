"""
文件导出 API - 发改委 XML / 商务部 Excel / 打包下载
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.schemas import MessageResponse
from app.middleware.auth import get_current_user, require_roles
from app.services.project_service import ProjectService
from app.services.export_engine import ExportEngine

router = APIRouter(prefix="/api/export", tags=["文件导出"])


@router.get("/{project_id}/ndrc-xml")
async def export_ndrc_xml(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.OPERATOR, UserRole.ADMIN])
    ),
):
    """导出发改委备案 XML"""
    project = await ProjectService.get_project(db, project_id, current_user.tenant_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    xml_bytes = await ExportEngine.generate_ndrc_xml(db, project)
    return StreamingResponse(
        io.BytesIO(xml_bytes),
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=ndrc_filing_{project_id}.xml"},
    )


@router.get("/{project_id}/mofcom-excel")
async def export_mofcom_excel(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.OPERATOR, UserRole.ADMIN])
    ),
):
    """导出商务部备案 Excel"""
    project = await ProjectService.get_project(db, project_id, current_user.tenant_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    excel_bytes = await ExportEngine.generate_mofcom_excel(db, project)
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=mofcom_filing_{project_id}.xlsx"},
    )


@router.get("/{project_id}/package")
async def export_package(
    project_id: UUID,
    export_type: str = Query("all", description="all / ndrc / mofcom"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles([UserRole.OPERATOR, UserRole.ADMIN])
    ),
):
    """一键打包下载"""
    project = await ProjectService.get_project(db, project_id, current_user.tenant_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    zip_bytes = await ExportEngine.generate_package(db, project, export_type)
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=odi_export_{project_id}.zip"},
    )
