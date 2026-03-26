"""
Dify 知识库服务 - 检索 + 对话（支持流式响应）
"""

import httpx
import logging
import json
from typing import Dict, List, Optional, Any, AsyncIterator
from app.config import settings

logger = logging.getLogger(__name__)


class DifyService:
    def __init__(self):
        self.api_key = settings.DIFY_API_KEY
        self.base_url = settings.DIFY_BASE_URL.rstrip("/")
        self.app_id = settings.DIFY_APP_ID
        self.dataset_id = settings.DIFY_DATASET_ID
        self.timeout = 120.0

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url and self.dataset_id)

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        if not self.is_configured or not self.app_id:
            return []

        chat_result = await self.chat(query=query, user_id="retrieve_user")

        if "error" in chat_result:
            logger.error(f"Dify retrieve failed: {chat_result['error']}")
            return []

        resources = chat_result.get("metadata", {}).get("retriever_resources", [])

        if not resources:
            return []

        chunks = []
        for r in resources:
            chunk_content = r.get("content", "")
            if chunk_content:
                chunks.append(
                    {
                        "content": chunk_content,
                        "score": r.get("score", 0.0),
                        "document_id": r.get("document_id"),
                        "dataset_id": r.get("dataset_id"),
                    }
                )

        logger.info(f"Dify retrieved {len(chunks)} chunks")
        return chunks

    async def chat(
        self,
        query: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Blocking 模式聊天 - 等待完整响应"""
        if not self.is_configured or not self.app_id:
            logger.warning("Dify not configured or app_id not set")
            return {"error": "Dify not configured"}

        url = f"{self.base_url}/v1/chat-messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": {},
            "query": query,
            "response_mode": "blocking",
            "user": user_id,
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code != 200:
                    logger.error(
                        f"Dify chat API error {resp.status_code}: {resp.text[:200]}"
                    )
                    return {"error": f"Dify API error: {resp.status_code}"}
                return resp.json()
        except httpx.ConnectError as e:
            logger.error(f"Dify connection error: {e}")
            return {"error": "Dify connection failed"}
        except httpx.ReadTimeout as e:
            logger.error(f"Dify read timeout: {e}")
            return {"error": "Dify 服务响应超时，请稍后重试"}
        except httpx.PoolTimeout as e:
            logger.error(f"Dify pool timeout: {e}")
            return {"error": "Dify 连接池超时，请稍后重试"}
        except Exception as e:
            logger.error(f"Dify chat error: {e}")
            return {"error": str(e)}

    async def chat_stream(
        self,
        query: str,
        user_id: str,
        conversation_id: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """流式聊天 - SSE 模式，边接收边 yield"""
        if not self.is_configured or not self.app_id:
            yield "error:Dify not configured"
            return

        url = f"{self.base_url}/v1/chat-messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "inputs": {},
            "query": query,
            "response_mode": "streaming",
            "user": user_id,
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                headers={"Accept": "text/event-stream"},
            ) as client:
                async with client.stream(
                    "POST", url, json=payload, headers=headers
                ) as resp:
                    if resp.status_code != 200:
                        error_text = await resp.text()
                        logger.error(
                            f"Dify stream error {resp.status_code}: {error_text[:200]}"
                        )
                        yield f"error:Dify API error: {resp.status_code}"
                        return

                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                event_data = json.loads(data)
                                event = event_data.get("event", "")
                                if event in (
                                    "message",
                                    "agent_message",
                                    "supercompletion",
                                ):
                                    content = event_data.get("answer", "")
                                    if content:
                                        yield content
                                elif event == "error":
                                    yield f"error:{event_data.get('message', 'Unknown error')}"
                                    break
                            except json.JSONDecodeError:
                                continue
        except httpx.ConnectError as e:
            logger.error(f"Dify stream connection error: {e}")
            yield "error:Dify connection failed"
        except httpx.ReadTimeout as e:
            logger.error(f"Dify stream read timeout: {e}")
            yield "error:Dify 服务响应超时，请稍后重试"
        except Exception as e:
            logger.error(f"Dify stream error: {e}")
            yield f"error:{str(e)}"

    def build_context_from_chunks(self, chunks: List[Dict]) -> str:
        if not chunks:
            return ""
        sections = []
        for i, chunk in enumerate(chunks, 1):
            content = chunk.get("content", "").strip()
            if content:
                sections.append(f"[文档{i}]\n{content}")
        return "\n\n".join(sections)


dify_service = DifyService()
