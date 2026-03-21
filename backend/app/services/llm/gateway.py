"""
LLM 网关 - 统一接口 + 工厂模式
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """LLM 统一响应"""

    content: str
    model: str
    provider: str
    usage: Dict[str, int] = None
    raw_response: Any = None


class BaseLLMProvider(ABC):
    """LLM 提供商基类"""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        """聊天补全"""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """检查服务可用性"""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass


class LLMGateway:
    """
    LLM 网关 - 工厂模式管理多个 LLM 提供商
    """

    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}

    def register_provider(self, name: str, provider: BaseLLMProvider):
        """注册 LLM 提供商"""
        self._providers[name] = provider
        # 防止重复注册后 provider 丢失（先删后加保证是最新的）
        if name in self._providers and self._providers[name] is not provider:
            self._providers[name] = provider

    def get_provider(self, name: str) -> Optional[BaseLLMProvider]:
        """获取指定提供商"""
        return self._providers.get(name)

    def list_providers(self) -> List[str]:
        """列出所有已注册的提供商"""
        return list(self._providers.keys())

    async def chat(
        self,
        provider_name: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        """通过网关调用指定提供商"""
        provider = self._providers.get(provider_name)
        if not provider:
            raise ValueError(f"未注册的 LLM 提供商: {provider_name}")
        return await provider.chat_completion(
            messages=messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        )


# 全局网关实例（延迟填充，lifespan 中初始化前均为空）
llm_gateway = LLMGateway()
