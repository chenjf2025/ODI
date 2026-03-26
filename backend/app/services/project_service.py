"""
项目服务 - CRUD + 状态机流转引擎
"""

from uuid import UUID
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import (
    ProjectInvestment,
    ProjectStatusLog,
    ProjectStatus,
    VALID_TRANSITIONS,
)
from app.models.entity import EntityDomestic, EntityOverseas
from app.schemas.schemas import ProjectCreate, ProjectStatusUpdate
from app.utils import utc_now


class ProjectService:
    @staticmethod
    async def create_project(
        db: AsyncSession,
        data: ProjectCreate,
        tenant_id: UUID,
        user_id: UUID,
    ) -> ProjectInvestment:
        project_name = data.project_name

        # 自动命名逻辑
        if not project_name and data.domestic_entity_id and data.overseas_entity_id:
            domestic = await db.get(EntityDomestic, data.domestic_entity_id)
            overseas = await db.get(EntityOverseas, data.overseas_entity_id)
            if domestic and overseas:
                project_name = f"{domestic.company_name}在{overseas.target_country}新设{overseas.overseas_name_cn}项目"

        if not project_name:
            project_name = f"ODI项目-{utc_now().strftime('%Y%m%d%H%M%S')}"

        project = ProjectInvestment(
            tenant_id=tenant_id,
            domestic_entity_id=data.domestic_entity_id,
            overseas_entity_id=data.overseas_entity_id,
            project_name=project_name,
            investment_amount=data.investment_amount,
            currency=data.currency,
            investment_path=data.investment_path,
            funding_source=data.funding_source,
            purpose_description=data.purpose_description,
            status=ProjectStatus.PRE_REVIEW,
            created_by=user_id,
        )
        db.add(project)
        await db.flush()

        # 自动生成项目编号
        year = utc_now().year
        seq_result = await db.execute(
            select(func.count())
            .select_from(ProjectInvestment)
            .where(
                ProjectInvestment.tenant_id == tenant_id,
                func.extract("year", ProjectInvestment.created_at) == year,
            )
        )
        seq = seq_result.scalar() + 1
        project.project_code = f"ODI-{year}-{seq:06d}"

        log = ProjectStatusLog(
            project_id=project.project_id,
            from_status=None,
            to_status=ProjectStatus.PRE_REVIEW,
            operator_id=user_id,
            remark="项目创建",
        )
        db.add(log)
        await db.flush()

        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(ProjectInvestment)
            .options(selectinload(ProjectInvestment.status_logs))
            .where(ProjectInvestment.project_id == project.project_id)
        )
        return result.scalar_one()

    @staticmethod
    async def get_project(
        db: AsyncSession, project_id: UUID, tenant_id: UUID
    ) -> Optional[ProjectInvestment]:
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(ProjectInvestment)
            .options(selectinload(ProjectInvestment.status_logs))
            .where(
                ProjectInvestment.project_id == project_id,
                ProjectInvestment.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_projects(
        db: AsyncSession,
        tenant_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None,
    ) -> tuple[List[ProjectInvestment], int]:
        from sqlalchemy.orm import selectinload

        query = (
            select(ProjectInvestment)
            .options(selectinload(ProjectInvestment.status_logs))
            .where(ProjectInvestment.tenant_id == tenant_id)
        )
        count_query = (
            select(func.count())
            .select_from(ProjectInvestment)
            .where(ProjectInvestment.tenant_id == tenant_id)
        )

        if status_filter:
            query = query.where(ProjectInvestment.status == status_filter)
            count_query = count_query.where(ProjectInvestment.status == status_filter)

        query = query.order_by(ProjectInvestment.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        total_result = await db.execute(count_query)
        return result.scalars().all(), total_result.scalar()

    @staticmethod
    async def transition_status(
        db: AsyncSession,
        project: ProjectInvestment,
        target_status_str: str,
        operator_id: UUID,
        remark: Optional[str] = None,
        ndrc_cert_url: Optional[str] = None,
        mofcom_cert_url: Optional[str] = None,
    ) -> ProjectInvestment:
        """状态机流转 - 校验合法性"""
        try:
            target_status = ProjectStatus(target_status_str)
        except ValueError:
            raise ValueError(f"无效的目标状态: {target_status_str}")

        current_status = (
            ProjectStatus(project.status)
            if isinstance(project.status, str)
            else project.status
        )
        valid_next = VALID_TRANSITIONS.get(current_status, [])

        if target_status not in valid_next:
            raise ValueError(
                f"非法状态转移: {current_status.value} -> {target_status.value}。"
                f"允许的下一状态: {[s.value for s in valid_next]}"
            )

        # 如果在推进时传入了证书 URL，则顺便保存
        if ndrc_cert_url:
            project.ndrc_certificate_url = ndrc_cert_url
        if mofcom_cert_url:
            project.mofcom_certificate_url = mofcom_cert_url

        # 特殊校验 - 发改委获批需上传备案通知书
        if (
            target_status == ProjectStatus.NDRC_APPROVED
            and not project.ndrc_certificate_url
        ):
            raise ValueError("发改委获批状态需先上传《备案通知书》")

        # 特殊校验 - 商务部获批需上传投资证书
        if (
            target_status == ProjectStatus.MOFCOM_APPROVED
            and not project.mofcom_certificate_url
        ):
            raise ValueError("商务部获批状态需先上传《企业境外投资证书》")

        old_status = current_status
        project.status = target_status
        project.updated_at = utc_now()

        log = ProjectStatusLog(
            project_id=project.project_id,
            from_status=old_status,
            to_status=target_status,
            operator_id=operator_id,
            remark=remark,
        )
        db.add(log)
        await db.flush()
        return project

    @staticmethod
    async def delete_project(db: AsyncSession, project: ProjectInvestment):
        await db.delete(project)
        await db.flush()

    @staticmethod
    async def submit_project(
        db: AsyncSession,
        project: ProjectInvestment,
        user_id: UUID,
    ) -> ProjectInvestment:
        if project.is_submitted:
            raise ValueError("项目已提交，无法重复提交")
        project.is_submitted = 1
        project.submitted_at = utc_now()
        project.submitted_by = user_id
        await db.flush()
        return project

    @staticmethod
    def can_edit_core_fields(project: ProjectInvestment) -> bool:
        return not project.is_submitted
