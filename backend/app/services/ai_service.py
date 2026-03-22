"""
AI 业务服务层 - 智能预审、报告生成、财务数据抽取
"""

import json
import re
from typing import Optional, Dict, List, Any
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


CONVERSATION_SYSTEM_PROMPT = """你是一个专业的 ODI 境外投资合规助手。你可以帮助用户：
1. 分析 ODI 项目的合规风险
2. 解答 ODI 备案相关问题（发改委、商务部、银行登记等流程）
3. 生成项目报告
4. 解答企业境外投资相关政策法规问题
5. 协助处理其他与境外投资相关的问题

请用专业但易懂的语言回答。如果用户的问题超出 ODI 领域，可以礼貌地引导回到相关话题。

如果需要执行操作（如生成报告、导出文件），请在回答末尾清楚地告诉用户操作结果。

当提供项目分析、规则命中等结构化信息时，请用 Markdown 表格或列表格式展示。"""


async def chat(
    db,
    tenant_id,
    user_id,
    messages: List[Dict[str, str]],
    attachments: Optional[List[Dict]] = None,
    context_project_id: Optional[str] = None,
    session_id=None,
) -> Dict[str, Any]:
    from app.services.intent_classifier import intent_classifier, Intent
    from app.services.action_executor import ActionExecutor
    from app.services.image_service import image_service

    last_user_message = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user_message = m.get("content", "")
            break

    classification = await intent_classifier.classify(last_user_message)
    intent = classification["intent"]
    entities = classification.get("entities", {})
    actions_results = []

    executor = ActionExecutor(db)

    if context_project_id and not entities.get("project_id"):
        entities["project_id"] = context_project_id

    response_text = None

    if intent == Intent.CLARIFY and classification.get("clarify_question"):
        response_text = classification["clarify_question"]

    elif intent == Intent.CREATE_PROJECT:
        project_name = entities.get("project_name")
        overseas_country = None
        m = re.search(r"去(.*?)投资", last_user_message)
        if m:
            overseas_country = m.group(1).strip()
        m2 = re.search(r"在(.*?)投资", last_user_message)
        if m2:
            overseas_country = m2.group(1).strip()

        if not overseas_country and not project_name:
            response_text = (
                "好的，要创建项目，请告诉我以下信息：\n"
                "1. 投资目的地是哪个国家/地区？\n"
                "2. 境内主体是哪家公司？（如果还没添加境内主体，请先到「境内主体管理」添加）"
            )
        else:
            project_data = {"project_name": project_name}
            if overseas_country:
                existing_overseas = await _find_or_create_overseas_entity(
                    db, tenant_id, overseas_country
                )
                if existing_overseas:
                    project_data["overseas_entity_id"] = existing_overseas.entity_id

            existing_domestic = await _find_single_domestic_entity(db, tenant_id)
            if existing_domestic:
                project_data["domestic_entity_id"] = existing_domestic.entity_id

            result = await executor.execute_create_project(
                tenant_id=tenant_id,
                user_id=user_id,
                project_data=project_data,
            )
            actions_results.append(result)
            if result.get("type") == "error":
                response_text = f"项目创建失败：{result.get('message')}"
            else:
                response_text = (
                    f"✅ 项目「{result['project_name']}」已创建成功！\n"
                    f"项目状态：{result['status']}\n"
                    f"项目ID：{result['project_id']}\n\n"
                    "您可以补充更多项目信息（投资金额、投资架构等），然后进行智能预审。"
                )

    elif intent == Intent.QUERY_PROJECT:
        if entities.get("project_id"):
            result = await executor.execute_project_detail(
                tenant_id, UUID(entities["project_id"])
            )
        else:
            result = await executor.execute_project_list(tenant_id)
        actions_results.append(result)
        response_text = _format_project_result(result)

    elif intent == Intent.PRE_REVIEW:
        project_id = entities.get("project_id") or context_project_id
        if not project_id:
            response_text = "请先选择一个项目，我才能为您进行预审分析。"
        else:
            result = await executor.execute_pre_review(
                tenant_id, UUID(project_id), ai_service
            )
            actions_results.append(result)
            if result.get("type") == "error":
                response_text = f"预审失败：{result.get('message')}"
            else:
                response_text = _format_pre_review_result(result)

    elif intent == Intent.GENERATE_REPORT:
        project_id = entities.get("project_id") or context_project_id
        report_type = entities.get("report_type") or "feasibility"
        if not project_id:
            response_text = "请先选择一个项目，我才能为您生成报告。"
        else:
            result = await executor.execute_generate_report(
                tenant_id, UUID(project_id), report_type, ai_service
            )
            actions_results.append(result)
            if result.get("type") == "error":
                response_text = f"报告生成失败：{result.get('message')}"
            else:
                content_preview = result.get("content", "")[:3000]
                response_text = f"报告已生成（类型：{report_type}），内容如下：\n\n{content_preview}..."

    elif intent in (Intent.EXPORT_NDRC, Intent.EXPORT_MOFCOM):
        project_id = entities.get("project_id") or context_project_id
        if not project_id:
            response_text = "请先选择一个项目，我才能为您导出文件。"
        else:
            if intent == Intent.EXPORT_NDRC:
                result = await executor.execute_export_ndrc(tenant_id, UUID(project_id))
            else:
                result = await executor.execute_export_mofcom(
                    tenant_id, UUID(project_id)
                )
            actions_results.append(result)
            if result.get("type") == "error":
                response_text = f"导出失败：{result.get('message')}"
            else:
                response_text = f"已为您生成{result.get('filename')}，文件已准备好。"

    elif intent == Intent.QUERY_ENTITY:
        result = await executor.execute_query_entity(
            tenant_id, entities.get("entity_name")
        )
        actions_results.append(result)
        response_text = _format_entity_result(result)

    elif intent == Intent.QUERY_RULES:
        result = await executor.execute_query_rules(tenant_id)
        actions_results.append(result)
        response_text = _format_rules_result(result)

    elif intent == Intent.KNOWLEDGE_QA:
        from app.services.dify_service import dify_service

        if not dify_service.is_configured:
            response_text = (
                "当前未配置 Dify 知识库服务，无法回答此类问题。"
                "请联系管理员配置 Dify API。"
            )
        else:
            chunks = await dify_service.retrieve(
                last_user_message, top_k=5, score_threshold=0.5
            )
            if dify_service.app_id:
                dify_result = await dify_service.chat(
                    query=last_user_message,
                    user_id=str(user_id),
                    conversation_id=None,
                )
                if "error" in dify_result:
                    response_text = f"Dify 服务调用失败：{dify_result['error']}"
                else:
                    response_text = dify_result.get("answer", "Dify 未返回有效响应")
                    actions_results.append({"type": "dify_chat", "chunks": chunks})
            else:
                context = dify_service.build_context_from_chunks(chunks)
                if context:
                    context_prompt = (
                        f"请根据以下知识库内容回答用户问题。如果知识库没有相关信息，请如实说明。\n\n"
                        f"【知识库内容】\n{context}\n\n【用户问题】{last_user_message}"
                    )
                    conversation_messages = [
                        {"role": "system", "content": CONVERSATION_SYSTEM_PROMPT},
                        {"role": "user", "content": context_prompt},
                    ]
                    try:
                        llm_response = await ai_service.router.route_and_call(
                            task_type=TaskType.GENERAL,
                            messages=conversation_messages,
                            temperature=0.7,
                            max_tokens=4096,
                        )
                        response_text = llm_response.content
                        ai_service.last_llm_usage = llm_response.usage
                    except Exception as e:
                        response_text = f"知识库检索成功，但 AI 生成失败：{str(e)}"
                else:
                    response_text = "知识库中未找到与您问题相关的内容。"

    if attachments and not response_text:
        extracted = await image_service.process_attachments(attachments)
        attachment_context = "\n".join(
            f"【{name}】: {text[:500]}" for name, text in extracted.items()
        )
        last_user_message += f"\n\n附件内容：\n{attachment_context}"

    if response_text is None:
        conversation_messages = [
            {"role": "system", "content": CONVERSATION_SYSTEM_PROMPT}
        ] + messages
        try:
            llm_response = await ai_service.router.route_and_call(
                task_type=TaskType.GENERAL,
                messages=conversation_messages,
                temperature=0.7,
                max_tokens=4096,
            )
            response_text = llm_response.content
            ai_service.last_llm_usage = llm_response.usage
        except Exception as e:
            response_text = f"抱歉，AI 服务暂时不可用：{str(e)}"
            ai_service.last_llm_usage = None

    return {
        "content": response_text,
        "intent": intent.value,
        "confidence": classification.get("confidence", 0.0),
        "actions": actions_results,
        "usage": ai_service.last_llm_usage,
    }


async def _find_or_create_overseas_entity(
    db: AsyncSession, tenant_id: UUID, country: str
):
    from sqlalchemy import select
    from app.models.entity import EntityOverseas

    result = await db.execute(
        select(EntityOverseas).where(
            EntityOverseas.tenant_id == tenant_id,
            EntityOverseas.target_country.ilike(f"%{country}%"),
        )
    )
    existing = result.scalars().first()
    return existing


async def _find_single_domestic_entity(db: AsyncSession, tenant_id: UUID):
    from sqlalchemy import select
    from app.models.entity import EntityDomestic

    result = await db.execute(
        select(EntityDomestic).where(EntityDomestic.tenant_id == tenant_id)
    )
    all_entities = result.scalars().all()
    if len(all_entities) == 1:
        return all_entities[0]
    return None


def _format_project_result(result: Dict) -> str:
    if result["type"] == "project_list":
        if not result["projects"]:
            return "您还没有创建任何 ODI 项目。"
        lines = ["| 项目名称 | 状态 | 金额 |", "|--------|------|-----|"]
        for p in result["projects"]:
            lines.append(
                f"| {p['name']} | {p['status']} | {p['amount']} {p['currency']} |"
            )
        return "以下是您的项目列表：\n" + "\n".join(lines)
    elif result["type"] == "project_detail":
        proj = result["project"]
        return f"**{proj['name']}**\n- 状态：{proj['status']}\n- 金额：{proj['amount']} {proj['currency']}\n- 投资架构：{proj['investment_path']}"
    return result.get("message", "项目信息加载失败")


def _format_pre_review_result(result: Dict) -> str:
    traffic_map = {"RED": "🔴 高风险", "YELLOW": "🟡 中风险", "GREEN": "🟢 低风险"}
    risk_text = traffic_map.get(result.get("traffic_light"), "未知")
    lines = [f"## {risk_text}  风险等级：{result.get('risk_level', '未知')}\n"]
    if result.get("matched_rules"):
        lines.append("### 命中规则：")
        for r in result["matched_rules"]:
            level = r.get("risk_level", "")
            name = r.get("rule_name") or r.get("target_value") or ""
            lines.append(f"- [{level}] {name}")
    if result.get("summary"):
        lines.append(f"\n### AI 分析\n{result['summary']}")
    if result.get("recommendations"):
        lines.append("\n### 建议措施")
        for rec in result["recommendations"]:
            lines.append(f"- {rec}")
    credits = result.get("credits_used", 0)
    lines.append(f"\n_本操作消耗 {credits} 点_")
    return "\n".join(lines)


def _format_entity_result(result: Dict) -> str:
    domestic = result.get("domestic", [])
    overseas = result.get("overseas", [])
    lines = []
    if domestic:
        lines.append("### 境内主体\n| 名称 | 信用代码 | 净资产 | 净利润 |")
        lines.append("|------|---------|-------|--------|")
        for e in domestic:
            lines.append(
                f"| {e['name']} | {e['uscc']} | {e['net_assets']} | {e['net_profit']} |"
            )
    if overseas:
        if lines:
            lines.append("")
        lines.append("### 境外标的\n| 中文名 | 英文名 | 目的国 | 行业 |")
        lines.append("|-------|--------|-------|------|")
        for e in overseas:
            lines.append(
                f"| {e['name_cn']} | {e['name_en']} | {e['country']} | {e['industry']} |"
            )
    return "未找到相关主体信息。" if not lines else "\n".join(lines)


def _format_rules_result(result: Dict) -> str:
    if not result.get("rules"):
        return "暂无可用的合规规则。"
    lines = [
        "### 合规规则列表\n",
        "| 规则描述 | 风险等级 | 类型 |",
        "|---------|---------|------|",
    ]
    for r in result["rules"]:
        lines.append(f"| {r['name']} | {r['risk_level']} | {r['rule_type']} |")
    return "\n".join(lines)
