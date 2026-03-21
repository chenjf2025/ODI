"""
DeepSeek API 客户端 - 核心逻辑判断与结构化生成
"""

from typing import List, Dict, Any
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.services.llm.gateway import BaseLLMProvider, LLMResponse


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek API 提供商"""

    @property
    def provider_name(self) -> str:
        return "deepseek"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError)
        ),
        reraise=True,
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs,
    ) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            if response.status_code == 429:
                raise httpx.RetryError("Rate limited")
            response.raise_for_status()
            data = response.json()

        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            model=data.get("model", self.model),
            provider=self.provider_name,
            usage=data.get("usage"),
            raw_response=data,
        )

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return response.status_code == 200
        except Exception:
            return False
