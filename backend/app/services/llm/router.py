"""
模型路由调度 - 根据任务类型分发到最合适的模型
"""

import logging
from enum import Enum
from typing import Dict, List, Optional

from app.exceptions import LLMAPIError
from app.services.llm.gateway import LLMGateway, LLMResponse, llm_gateway

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """AI 任务类型"""

    DOCUMENT_PARSE = "DOCUMENT_PARSE"  # 文档长文本解析 -> Kimi
    LOGIC_JUDGE = "LOGIC_JUDGE"  # 核心逻辑判断 -> DeepSeek
    REPORT_GENERATE = "REPORT_GENERATE"  # 报告润色生成 -> MiniMax / DeepSeek
    DATA_EXTRACT = "DATA_EXTRACT"  # 财务数据抽取 -> Kimi
    GENERAL = "GENERAL"  # 通用任务 -> DeepSeek


# 默认任务类型 -> 提供商偏好顺序
DEFAULT_ROUTING = {
    TaskType.DOCUMENT_PARSE: ["kimi", "deepseek", "minimax"],
    TaskType.LOGIC_JUDGE: ["deepseek", "kimi", "minimax"],
    TaskType.REPORT_GENERATE: ["deepseek", "minimax", "kimi"],
    TaskType.DATA_EXTRACT: ["kimi", "deepseek", "minimax"],
    TaskType.GENERAL: ["deepseek", "kimi", "minimax"],
}


class LLMRouter:
    """
    模型路由调度器 - 根据任务类型选择最优模型，支持降级
    """

    def __init__(self, gateway: LLMGateway = None):
        self.gateway = gateway or llm_gateway
        self.routing_table: Dict[TaskType, List[str]] = DEFAULT_ROUTING.copy()

    def set_routing(self, task_type: TaskType, providers: List[str]):
        """自定义路由规则"""
        self.routing_table[task_type] = providers

    async def route_and_call(
        self,
        task_type: TaskType,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        """
        根据任务类型路由到最优模型，失败自动降级。
        先按偏好列表尝试，再补充列表中未提及的已注册提供商。
        """
        preferred = self.routing_table.get(task_type, [])
        # 将所有已注册但不在偏好列表中的提供商追加到末尾，确保完整降级
        all_registered = self.gateway.list_providers()
        candidates = list(preferred) + [p for p in all_registered if p not in preferred]

        last_error = None

        for provider_name in candidates:
            provider = self.gateway.get_provider(provider_name)
            if not provider:
                continue
            try:
                logger.info(f"LLM 路由: {task_type.value} -> {provider_name}")
                return await provider.chat_completion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
            except Exception as e:
                logger.warning(f"LLM 提供商 {provider_name} 调用失败: {e}")
                last_error = str(e)
                continue

        available = [p for p in candidates if self.gateway.get_provider(p)]
        raise LLMAPIError(
            message=f"所有模型提供商均不可用 (任务类型: {task_type.value})",
            providers=available,
            last_error=last_error or "无",
        )


# 全局路由器实例
llm_router = LLMRouter()
