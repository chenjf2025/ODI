"""
Dify 知识库服务 - 检索 + 对话
"""

import httpx
from typing import Dict, List, Optional, Any
from app.config import settings


class DifyService:
    def __init__(self):
        self.api_key = settings.DIFY_API_KEY
        self.base_url = settings.DIFY_BASE_URL.rstrip("/")
        self.app_id = settings.DIFY_APP_ID
        self.dataset_id = settings.DIFY_DATASET_ID
        self.timeout = 30.0

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url)

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
    ) -> List[Dict[str, Any]]:
        if not self.is_configured:
            return []
        if not self.dataset_id:
            return []

        url = f"{self.base_url}/datasets/{self.dataset_id}/retrieve"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": {"content": query},
            "records": [],
            "retrieval_setting": {
                "top_k": top_k,
                "score_threshold": score_threshold,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                return []
            data = resp.json()
            records = data.get("records", [])
            return [
                {
                    "content": r.get("segment", {}).get("content", ""),
                    "score": r.get("score", 0.0),
                    "document_id": r.get("segment", {}).get("document_id"),
                }
                for r in records
                if r.get("segment", {}).get("content")
            ]

    async def chat(
        self,
        query: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.is_configured or not self.app_id:
            return {"error": "Dify not configured"}

        url = f"{self.base_url}/v1/chat-messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        inputs = {"message": query}
        if context:
            inputs["context"] = context

        payload = {
            "inputs": inputs,
            "response_mode": "blocking",
            "user": user_id,
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                return {"error": f"Dify API error: {resp.status_code}"}
            return resp.json()

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
