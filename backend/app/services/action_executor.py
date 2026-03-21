"""
操作执行器 - 执行 AI 意图识别后触发的各类操作
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
import io
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.project import ProjectInvestment, ProjectStatus
from app.models.entity import EntityDomestic, EntityOverseas
from app.models.tenant import Tenant
from app.models.rules import RulesEngine
from app.services.project_service import ProjectService
from app.services.export_engine import ExportEngine


class ActionExecutor:
    """
    执行 AI 触发的各类操作，返回操作结果
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_project_list(
        self, tenant_id: UUID, limit: int = 10
    ) -> Dict[str, Any]:
        """列出项目"""
        result = await self.db.execute(
            select(ProjectInvestment)
            .where(ProjectInvestment.tenant_id == tenant_id)
            .order_by(ProjectInvestment.created_at.desc())
            .limit(limit)
        )
        projects = result.scalars().all()
        return {
            "type": "project_list",
            "count": len(projects),
            "projects": [
                {
                    "id": str(p.project_id),
                    "name": p.project_name,
                    "status": p.status.value
                    if hasattr(p.status, "value")
                    else p.status,
                    "amount": p.investment_amount,
                    "currency": p.currency.value
                    if hasattr(p.currency, "value")
                    else p.currency,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in projects
            ],
        }

    async def execute_project_detail(
        self, tenant_id: UUID, project_id: UUID
    ) -> Dict[str, Any]:
        """获取项目详情"""
        project = await ProjectService.get_project(self.db, project_id, tenant_id)
        if not project:
            return {"type": "error", "message": "项目不存在"}

        return {
            "type": "project_detail",
            "project": {
                "id": str(project.project_id),
                "name": project.project_name,
                "status": project.status.value
                if hasattr(project.status, "value")
                else project.status,
                "amount": project.investment_amount,
                "currency": project.currency.value
                if hasattr(project.currency, "value")
                else project.currency,
                "investment_path": project.investment_path.value
                if hasattr(project.investment_path, "value")
                else project.investment_path,
                "purpose": project.purpose_description,
                "created_at": project.created_at.isoformat()
                if project.created_at
                else None,
                "pre_review_report": project.pre_review_report,
                "feasibility_report": project.feasibility_report,
                "due_diligence_report": project.due_diligence_report,
            },
        }

    async def execute_pre_review(
        self, tenant_id: UUID, project_id: UUID, ai_service
    ) -> Dict[str, Any]:
        """执行智能预审"""
        from app.services.billing_service import BillingService

        project = await ProjectService.get_project(self.db, project_id, tenant_id)
        if not project:
            return {"type": "error", "message": "项目不存在"}

        tenant = await self.db.get(Tenant, tenant_id)
        if not tenant:
            return {"type": "error", "message": "租户不存在"}

        # 先做余额预检
        if (
            tenant.subscription_plan.value != "ANNUAL"
            if hasattr(tenant.subscription_plan, "value")
            else str(tenant.subscription_plan) != "ANNUAL"
        ):
            if tenant.balance_credits < 1:
                return {
                    "type": "error",
                    "message": f"点数余额不足（当前 {tenant.balance_credits} 点），无法执行预审",
                    "error_code": "INSUFFICIENT_FUNDS",
                }

        # 调用预审
        report = await ai_service.pre_review(self.db, project)

        # 扣点（按实际token）
        await BillingService.check_and_deduct(
            self.db,
            tenant,
            project.project_id,
            "AI 智能预审",
            usage=ai_service.last_llm_usage,
        )

        return {
            "type": "pre_review_result",
            "project_id": str(project_id),
            "risk_level": report.get("risk_level", ""),
            "traffic_light": report.get("traffic_light", "GREEN"),
            "matched_rules": report.get("matched_rules", []),
            "summary": report.get("ai_analysis", ""),
            "recommendations": report.get("recommendations", []),
            "asset_warning": report.get("asset_warning"),
            "credits_used": max(
                1, (ai_service.last_llm_usage.get("total_tokens", 0) // 1000)
            )
            if ai_service.last_llm_usage
            else 1,
        }

    async def execute_generate_report(
        self,
        tenant_id: UUID,
        project_id: UUID,
        report_type: str,
        ai_service,
    ) -> Dict[str, Any]:
        """执行报告生成"""
        from app.services.billing_service import BillingService

        project = await ProjectService.get_project(self.db, project_id, tenant_id)
        if not project:
            return {"type": "error", "message": "项目不存在"}

        tenant = await self.db.get(Tenant, tenant_id)
        if not tenant:
            return {"type": "error", "message": "租户不存在"}

        if report_type not in ("feasibility", "due_diligence"):
            return {"type": "error", "message": f"不支持的报告类型: {report_type}"}

        # 生成报告
        if report_type == "feasibility":
            content = await ai_service.generate_feasibility_report(self.db, project)
        else:
            content = await ai_service.generate_due_diligence_report(self.db, project)

        # 扣点
        await BillingService.check_and_deduct(
            self.db,
            tenant,
            project.project_id,
            f"AI 生成{report_type}报告",
            usage=ai_service.last_llm_usage,
        )

        return {
            "type": "report_generated",
            "project_id": str(project_id),
            "report_type": report_type,
            "content": content,
            "credits_used": max(
                1, (ai_service.last_llm_usage.get("total_tokens", 0) // 1000)
            )
            if ai_service.last_llm_usage
            else 1,
        }

    async def execute_export_ndrc(
        self, tenant_id: UUID, project_id: UUID
    ) -> Dict[str, Any]:
        """导出发改委 XML"""
        project = await ProjectService.get_project(self.db, project_id, tenant_id)
        if not project:
            return {"type": "error", "message": "项目不存在"}

        xml_bytes = await ExportEngine.generate_ndrc_xml(self.db, project)
        # 返回 base64 编码
        import base64

        return {
            "type": "export_file",
            "format": "ndrc_xml",
            "filename": f"发改委备案_{project.project_name}.xml",
            "content_base64": base64.b64encode(xml_bytes).decode("utf-8"),
            "content": xml_bytes.decode("utf-8", errors="replace"),
        }

    async def execute_export_mofcom(
        self, tenant_id: UUID, project_id: UUID
    ) -> Dict[str, Any]:
        """导出商务部 Excel"""
        project = await ProjectService.get_project(self.db, project_id, tenant_id)
        if not project:
            return {"type": "error", "message": "项目不存在"}

        excel_bytes = await ExportEngine.generate_mofcom_excel(self.db, project)
        import base64

        return {
            "type": "export_file",
            "format": "mofcom_excel",
            "filename": f"商务部备案_{project.project_name}.xlsx",
            "content_base64": base64.b64encode(excel_bytes).decode("utf-8"),
        }

    async def execute_query_entity(
        self, tenant_id: UUID, entity_name: str = None, entity_type: str = "all"
    ) -> Dict[str, Any]:
        """查询主体信息"""
        results = {"domestic": [], "overseas": []}

        if entity_type in ("all", "domestic"):
            result = await self.db.execute(
                select(EntityDomestic)
                .where(EntityDomestic.tenant_id == tenant_id)
                .order_by(EntityDomestic.created_at.desc())
            )
            domestic = result.scalars().all()
            if entity_name:
                domestic = [
                    d for d in domestic if entity_name in (d.company_name or "")
                ]
            results["domestic"] = [
                {
                    "id": str(e.entity_id),
                    "name": e.company_name,
                    "uscc": e.uscc,
                    "net_assets": e.net_assets,
                    "net_profit": e.net_profit,
                }
                for e in domestic
            ]

        if entity_type in ("all", "overseas"):
            result = await self.db.execute(
                select(EntityOverseas)
                .where(EntityOverseas.tenant_id == tenant_id)
                .order_by(EntityOverseas.created_at.desc())
            )
            overseas = result.scalars().all()
            if entity_name:
                overseas = [
                    o
                    for o in overseas
                    if entity_name in (o.overseas_name_cn or "")
                    or entity_name in (o.overseas_name_en or "")
                ]
            results["overseas"] = [
                {
                    "id": str(e.entity_id),
                    "name_cn": e.overseas_name_cn,
                    "name_en": e.overseas_name_en,
                    "country": e.target_country,
                    "industry": e.overseas_industry_code,
                }
                for e in overseas
            ]

        return {"type": "entity_list", **results}

    async def execute_query_rules(self, tenant_id: UUID = None) -> Dict[str, Any]:
        """查询合规规则"""
        result = await self.db.execute(select(RulesEngine))
        rules = result.scalars().all()
        return {
            "type": "rules_list",
            "count": len(rules),
            "rules": [
                {
                    "id": str(r.rule_id),
                    "name": r.description or r.target_value,
                    "risk_level": r.risk_level.value
                    if hasattr(r.risk_level, "value")
                    else r.risk_level,
                    "rule_type": r.rule_type.value
                    if hasattr(r.rule_type, "value")
                    else r.rule_type,
                    "target_value": r.target_value,
                }
                for r in rules
            ],
        }

    async def execute_create_project(
        self,
        tenant_id: UUID,
        user_id: UUID,
        project_data: Dict,
    ) -> Dict[str, Any]:
        """创建项目"""
        from app.schemas.schemas import ProjectCreate

        data = ProjectCreate(**project_data)
        project = await ProjectService.create_project(self.db, data, tenant_id, user_id)
        return {
            "type": "project_created",
            "project_id": str(project.project_id),
            "project_name": project.project_name,
            "status": project.status.value
            if hasattr(project.status, "value")
            else project.status,
        }
