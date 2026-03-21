"""
图片理解服务 - 支持 OCR 文字提取 + 图片内容理解
"""

from typing import Optional, Dict, List
import base64
import io

from app.services.llm.router import LLMRouter, TaskType, llm_router


class ImageService:
    """
    图片处理：OCR 文字提取 + LLM 图片内容理解
    """

    def __init__(self, router: LLMRouter = None):
        self.router = router or llm_router

    async def extract_text_from_image(self, image_base64: str) -> str:
        """
        使用 LLM vision 理解图片中的文字内容（当 LLM 支持 vision 时），
        或直接返回图片描述。
        目前通过通用 LLM 对图片做 OCR-like 理解。
        """
        image_data = f"data:image/jpeg;base64,{image_base64}"

        try:
            response = await self.router.route_and_call(
                task_type=TaskType.DOCUMENT_PARSE,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": image_data},
                            },
                            {
                                "type": "text",
                                "text": "请描述这张图片中的所有文字内容，保持原有结构。如果是表格请还原表格。如果是证件或文件请提取关键字段。",
                            },
                        ],
                    }
                ],
                temperature=0.1,
                max_tokens=4096,
            )
            return response.content
        except Exception as e:
            return f"[图片理解失败: {str(e)}]"

    async def describe_image(self, image_base64: str) -> str:
        """
        对图片进行描述（用于确认上传的内容）
        """
        image_data = f"data:image/jpeg;base64,{image_base64}"

        try:
            response = await self.router.route_and_call(
                task_type=TaskType.DOCUMENT_PARSE,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": image_data},
                            },
                            {
                                "type": "text",
                                "text": "请简洁描述这张图片的内容（1-2句话），不要解释，只描述。",
                            },
                        ],
                    }
                ],
                temperature=0.1,
                max_tokens=256,
            )
            return response.content
        except Exception as e:
            return f"[图片描述失败: {str(e)}]"

    async def process_attachments(self, attachments: List[Dict]) -> Dict[str, str]:
        """
        处理一批附件（图片/文件），返回 {name: extracted_text}
        """
        results = {}

        for att in attachments:
            att_type = att.get("type", "unknown")
            name = att.get("name", f"attachment_{att_type}")

            if att_type == "image":
                image_data = att.get("url", "")
                if image_data.startswith("data:"):
                    # 去掉 data:image/xxx;base64, 前缀
                    image_data = image_data.split(",", 1)[1]

                text = await self.extract_text_from_image(image_data)
                results[name] = text

            elif att_type == "file":
                # 文件类附件暂不支持处理
                results[name] = f"[文件 {name} 已上传，内容待解析]"

            elif att_type == "text":
                results[name] = att.get("content", "")

        return results


# 全局实例
image_service = ImageService()
