"""
意图分类器 - 将用户自然语言映射到系统操作
"""

import json
from enum import Enum
from typing import Dict, List, Optional
from app.services.llm.router import LLMRouter, TaskType, llm_router


class Intent(str, Enum):
    """支持的意图类型"""

    CREATE_PROJECT = "create_project"
    QUERY_PROJECT = "query_project"
    PRE_REVIEW = "pre_review"
    GENERATE_REPORT = "generate_report"
    EXPORT_NDRC = "export_ndrc"
    EXPORT_MOFCOM = "export_mofcom"
    QUERY_ENTITY = "query_entity"
    QUERY_RULES = "query_rules"
    KNOWLEDGE_QA = "knowledge_qa"
    GENERAL_CHAT = "general_chat"
    CLARIFY = "clarify"


INTENT_CLASSIFIER_PROMPT = """你是一个意图分类器。请根据用户输入判断其意图。

支持的意图类型：
- create_project: 创建新ODI项目
- query_project: 查询项目信息或列表
- pre_review: 对项目进行智能预审
- generate_report: 生成可研报告或尽调报告
- export_ndrc: 导出发改委XML备案文件
- export_mofcom: 导出商务部Excel备案文件
- query_entity: 查询境内主体或境外标的信息
- query_rules: 查询合规规则
- knowledge_qa: 询问ODI备案知识、法规、政策（适合知识库检索）
- general_chat: 通用聊天、寒暄、关于平台本身的询问
- clarify: 意图模糊，需要追问

用户输入：{user_input}

请以JSON格式输出，格式如下（不要输出其他内容）：
{{"intent": "意图类型", "entities": {{"project_name": "如果提到项目名则填入", "entity_name": "如果提到主体名则填入", "report_type": "feasibility或due_diligence，如果意图是generate_report"}}, "confidence": 0.0-1.0, "needs_clarify": true或false, "clarify_question": "如果needs_clarify为true，填写追问问题"}}

示例：
输入："帮我分析一下新加坡项目的风险"
输出：{{"intent": "pre_review", "entities": {{"project_name": "新加坡项目"}}, "confidence": 0.95, "needs_clarify": false, "clarify_question": null}}

输入："生成报告"
输出：{{"intent": "generate_report", "entities": {{"report_type": "feasibility"}}, "confidence": 0.7, "needs_clarify": true, "clarify_question": "您需要生成哪种报告？可行性研究报告还是尽职调查报告？"}}

输入："你好"
输出：{{"intent": "general_chat", "entities": {{}}, "confidence": 1.0, "needs_clarify": false, "clarify_question": null}}
"""


class IntentClassifier:
    """
    LLM 驱动的意图分类器
    """

    def __init__(self, router: LLMRouter = None):
        self.router = router or llm_router

    async def classify(self, user_input: str) -> Dict:
        """
        分类用户输入，返回意图及实体信息
        """
        prompt = INTENT_CLASSIFIER_PROMPT.format(user_input=user_input)

        try:
            response = await self.router.route_and_call(
                task_type=TaskType.LOGIC_JUDGE,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的意图分类助手。请严格按JSON格式输出，不要添加任何解释。",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=512,
            )

            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            result = json.loads(content)
            return {
                "intent": Intent(result.get("intent", "general_chat")),
                "entities": result.get("entities", {}),
                "confidence": result.get("confidence", 0.5),
                "needs_clarify": result.get("needs_clarify", False),
                "clarify_question": result.get("clarify_question"),
            }
        except Exception as e:
            return {
                "intent": Intent.GENERAL_CHAT,
                "entities": {},
                "confidence": 0.0,
                "needs_clarify": False,
                "clarify_question": None,
                "error": str(e),
            }


# 全局实例
intent_classifier = IntentClassifier()
