"""
应用配置管理 - 读取环境变量
"""

import logging
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional

logger = logging.getLogger(__name__)


def _find_env_file() -> str:
    """查找 .env 文件: 先找项目根目录、再找当前目录"""
    candidates = [
        Path(__file__).resolve().parent.parent.parent / ".env.development",
        Path(__file__).resolve().parent.parent / ".env.development",
        Path("/app/.env.development"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return ""


class Settings(BaseSettings):
    # 数据库
    DATABASE_URL: str = (
        "postgresql+asyncpg://odi_user:odi_pass_dev@localhost:5432/odi_saas_dev"
    )
    DATABASE_SYNC_URL: str = (
        "postgresql://odi_user:odi_pass_dev@localhost:5432/odi_saas_dev"
    )

    # JWT
    JWT_SECRET_KEY: str = ""  # 生产环境必填，开发环境可为空
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: str = ""  # 生产环境禁止包含 localhost，生产部署时必须显式配置

    # AI 模型
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    KIMI_API_KEY: str = ""
    KIMI_BASE_URL: str = "https://api.moonshot.cn/v1"
    MINIMAX_API_KEY: str = ""
    MINIMAX_BASE_URL: str = "https://api.minimax.chat/v1"

    # 企业征信
    QICHACHA_API_KEY: str = ""
    TIANYANCHA_API_KEY: str = ""
    BAIDU_CREDIT_API_KEY: str = ""
    DEFAULT_CORP_INFO_PROVIDER: str = "qichacha"

    # 应用
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # ==================== Pydantic Validators ====================

    @field_validator("JWT_SECRET_KEY", mode="after")
    @classmethod
    def _check_jwt_secret(cls, v: str) -> str:
        """生产环境 (APP_ENV=production) 禁止空 JWT_SECRET_KEY"""
        app_env = os.environ.get("APP_ENV", "development")
        if app_env == "production" and (not v or not v.strip()):
            raise ValueError(
                "JWT_SECRET_KEY 在生产环境 (APP_ENV=production) 中必须设置，不能为空"
            )
        return v

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def _check_cors_no_localhost_in_production(cls, v: str) -> str:
        """生产环境禁止 CORS_ORIGINS 包含 localhost / 127.0.0.1"""
        app_env = os.environ.get("APP_ENV", "development")
        if app_env == "production" and v:
            lowered = v.lower()
            if "localhost" in lowered or "127.0.0.1" in lowered:
                raise ValueError(
                    f"CORS_ORIGINS 在生产环境 (APP_ENV=production) 中禁止包含 localhost 或 127.0.0.1。当前值: {v}"
                )
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.CORS_ORIGINS:
            return []
        return [
            origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()
        ]

    class Config:
        env_file = _find_env_file()
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
