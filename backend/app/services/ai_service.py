"""
AI 业务服务层 - 智能预审、报告生成、财务数据抽取
"""

import json
from typing import Optional, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import ProjectInvestment
from app.models.entity import EntityDomestic, EntityOverseas
from app.services.llm.router import LLMRouter, TaskType, llm_router
from app.services.rules_service import RulesService
from app.utils import utc_now


class AIService:
    def __init__(self, router: LLMRouter = None):
        self.router = router or llm_router
        self.last_llm_usage: Optional[Dict[str, int]] = (
            None  # 最近一次 LLM 调用的 token 使用量
        )

    async def pre_review(
        self,
        db: AsyncSession,
        project: ProjectInvestment,
    ) -> dict:
        """
        智能预审：合规规则 + LLM 综合判断
        """
        # 1. 先用规则引擎匹配
        overseas_entity = None
        domestic_entity = None
        if project.overseas_entity_id:
            overseas_entity = await db.get(EntityOverseas, project.overseas_entity_id)
        if project.domestic_entity_id:
            domestic_entity = await db.get(EntityDomestic, project.domestic_entity_id)

        target_country = overseas_entity.target_country if overseas_entity else None
        industry_code = (
            overseas_entity.overseas_industry_code if overseas_entity else None
        )

        rules_result = await RulesService.match_rules(db, target_country, industry_code)

        # 2. 净资产校验 (净资产必须大于拟投资总额)
        asset_warning = None
        if domestic_entity and project.investment_amount:
            if (
                domestic_entity.net_assets
                and domestic_entity.net_assets < project.investment_amount
            ):
                asset_warning = (
                    f"⚠️ 警告：境内主体最近一年净资产({domestic_entity.net_assets})小于"
                    f"拟投资总额({project.investment_amount})，可能无法通过备案审核。"
                )

        # 3. 调用 LLM 生成综合预审意见
        prompt = self._build_pre_review_prompt(
            project, domestic_entity, overseas_entity, rules_result, asset_warning
        )

        try:
            llm_response = await self.router.route_and_call(
                task_type=TaskType.LOGIC_JUDGE,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位专业的境外投资合规分析师，精通中国企业境外直接投资(ODI)备案法规。请基于提供的信息进行专业的预审分析。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=4096,
            )
            self.last_llm_usage = llm_response.usage
            ai_analysis = llm_response.content
        except Exception as e:
            self.last_llm_usage = None
            ai_analysis = f"AI 分析暂不可用，请稍后重试或联系管理员。错误信息: {type(e).__name__}: {str(e)}"

        # 4. 组装预审报告
        report = {
            "project_name": project.project_name,
            "review_time": utc_now().isoformat(),
            "risk_level": rules_result["overall_risk"],
            "traffic_light": rules_result["traffic_light"],
            "matched_rules": rules_result["matched_rules"],
            "asset_warning": asset_warning,
            "ai_analysis": ai_analysis,
            "recommendations": self._extract_recommendations(rules_result),
        }

        # 保存到项目
        project.pre_review_report = report
        await db.flush()

        return report

    async def generate_feasibility_report(
        self,
        db: AsyncSession,
        project: ProjectInvestment,
    ) -> str:
        """生成可行性研究报告"""
        domestic_entity = None
        overseas_entity = None
        if project.domestic_entity_id:
            domestic_entity = await db.get(EntityDomestic, project.domestic_entity_id)
        if project.overseas_entity_id:
            overseas_entity = await db.get(EntityOverseas, project.overseas_entity_id)

        prompt = self._build_feasibility_prompt(
            project, domestic_entity, overseas_entity
        )

        llm_response = await self.router.route_and_call(
            task_type=TaskType.REPORT_GENERATE,
            messages=[
                {
                    "role": "system",
                    "content": "你是一位资深的投资分析专家，擅长撰写境外投资项目可行性研究报告。请使用正式的公文语言风格，结构清晰，论据充分。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=8192,
        )
        self.last_llm_usage = llm_response.usage

        project.feasibility_report = llm_response.content
        await db.flush()
        return llm_response.content

    async def generate_due_diligence_report(
        self,
        db: AsyncSession,
        project: ProjectInvestment,
    ) -> str:
        """生成尽职调查报告"""
        domestic_entity = None
        overseas_entity = None
        if project.domestic_entity_id:
            domestic_entity = await db.get(EntityDomestic, project.domestic_entity_id)
        if project.overseas_entity_id:
            overseas_entity = await db.get(EntityOverseas, project.overseas_entity_id)

        prompt = self._build_due_diligence_prompt(
            project, domestic_entity, overseas_entity
        )

        llm_response = await self.router.route_and_call(
            task_type=TaskType.REPORT_GENERATE,
            messages=[
                {
                    "role": "system",
                    "content": "你是一位专业的尽职调查分析师，擅长撰写境外投资项目尽职调查报告。请使用严谨专业的语言，全面覆盖各项调查要素。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=8192,
        )
        self.last_llm_usage = llm_response.usage

        project.due_diligence_report = llm_response.content
        await db.flush()
        return llm_response.content

    async def extract_financial_data(
        self,
        text_content: str,
    ) -> dict:
        """从审计报告文本中抽取财务数据"""
        prompt = f"""请从以下财务报告或审计报告文本中，抽取关键财务指标，并以严格的 JSON 格式输出。

需要抽取的指标：
- net_assets: 净资产（元）
- net_profit: 净利润（元）
- total_revenue: 总营收（元）
- total_assets: 总资产（元）
- total_liabilities: 总负债（元）
- operating_profit: 营业利润（元）

如果某项指标在文本中未找到，对应值为 null。

文本内容：
---
{text_content[:50000]}
---

请仅输出 JSON，不要添加任何其他文字或 markdown 标记。
"""

        llm_response = await self.router.route_and_call(
            task_type=TaskType.DATA_EXTRACT,
            messages=[
                {
                    "role": "system",
                    "content": "你是专业的财务数据抽取助手。请严格按照 JSON 格式输出结构化数据。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=2048,
        )

        try:
            content = llm_response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw_output": llm_response.content, "parse_error": True}

    # ==================== 私有方法 - Prompt 构建 ====================

    def _build_pre_review_prompt(
        self, project, domestic, overseas, rules_result, asset_warning
    ):
        parts = ["请对以下 ODI 境外投资项目进行合规预审分析：\n"]
        parts.append(f"项目名称：{project.project_name}")
        parts.append(f"拟投资金额：{project.investment_amount} {project.currency}")
        parts.append(f"投资架构：{project.investment_path}")
        if project.purpose_description:
            parts.append(f"投资目的：{project.purpose_description}")

        if domestic:
            parts.append(f"\n境内主体：{domestic.company_name}")
            parts.append(f"统一信用代码：{domestic.uscc}")
            parts.append(f"净资产：{domestic.net_assets}")
            parts.append(f"净利润：{domestic.net_profit}")

        if overseas:
            parts.append(
                f"\n境外标的：{overseas.overseas_name_cn} ({overseas.overseas_name_en})"
            )
            parts.append(f"目的国/地区：{overseas.target_country}")
            parts.append(f"境外行业：{overseas.overseas_industry_code}")

        if rules_result["matched_rules"]:
            parts.append(f"\n已命中 {len(rules_result['matched_rules'])} 条合规规则：")
            for r in rules_result["matched_rules"]:
                parts.append(
                    f"  - [{r['risk_level']}] {r.get('rule_name', r['target_value'])}: {r.get('description', '')}"
                )

        if asset_warning:
            parts.append(f"\n{asset_warning}")

        parts.append(
            "\n请分析：1.合规风险等级 2.核心风险点 3.建议措施 4.备案可行性结论"
        )
        return "\n".join(parts)

    def _build_feasibility_prompt(self, project, domestic, overseas):
        parts = ["请根据以下信息撰写一份完整的《境外投资项目可行性研究报告》：\n"]
        parts.append(f"项目名称：{project.project_name}")
        parts.append(f"投资金额：{project.investment_amount} {project.currency}")
        parts.append(f"投资架构：{project.investment_path}")
        if project.funding_source:
            parts.append(
                f"资金来源：{json.dumps(project.funding_source, ensure_ascii=False)}"
            )
        if project.purpose_description:
            parts.append(f"投资背景与目的：{project.purpose_description}")

        if domestic:
            parts.append(f"\n投资方：{domestic.company_name}（{domestic.uscc}）")
            parts.append(
                f"最近一年净资产：{domestic.net_assets}元，净利润：{domestic.net_profit}元"
            )

        if overseas:
            parts.append(
                f"\n被投方：{overseas.overseas_name_cn} ({overseas.overseas_name_en})"
            )
            parts.append(f"注册地：{overseas.target_country}")
            parts.append(f"主营业务代码：{overseas.overseas_industry_code}")
            parts.append(f"注册资本：{overseas.registered_capital} {overseas.currency}")

        parts.append(
            "\n报告需包含：项目概况、投资必要性分析、市场分析、投资方案、财务分析、"
            "风险分析及对策、经济和社会效益分析、可行性结论等章节。"
        )
        return "\n".join(parts)

    def _build_due_diligence_prompt(self, project, domestic, overseas):
        parts = ["请根据以下信息撰写一份完整的《境外投资尽职调查报告》：\n"]
        parts.append(f"项目名称：{project.project_name}")

        if domestic:
            parts.append(f"\n投资方基本情况：{domestic.company_name}")
            parts.append(f"统一信用代码：{domestic.uscc}")

        if overseas:
            parts.append(
                f"\n标的公司：{overseas.overseas_name_cn} ({overseas.overseas_name_en})"
            )
            parts.append(f"注册地：{overseas.target_country}")
            parts.append(f"注册资本：{overseas.registered_capital} {overseas.currency}")

        parts.append(f"\n投资金额：{project.investment_amount} {project.currency}")
        parts.append(f"投资架构：{project.investment_path}")

        parts.append(
            "\n报告需包含：标的公司概况、股权结构、财务状况、法律合规、"
            "税务分析、经营情况、主要风险、估值分析、调查结论等章节。"
        )
        return "\n".join(parts)

    def _extract_recommendations(self, rules_result):
        recs = []
        for rule in rules_result["matched_rules"]:
            if rule.get("trigger_action"):
                action = rule["trigger_action"]
                if isinstance(action, dict):
                    if "recommendation" in action:
                        recs.append(action["recommendation"])
                    if "warning" in action:
                        recs.append(action["warning"])
                elif isinstance(action, str):
                    recs.append(action)
        return recs


# 全局 AI 服务实例
ai_service = AIService()
