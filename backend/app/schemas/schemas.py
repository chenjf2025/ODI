"""
Pydantic 请求/响应模式定义
"""

from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, List, Any, Dict
from datetime import datetime
from uuid import UUID
from enum import Enum


# ==================== 认证相关 ====================


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user_id: str
    role: str
    tenant_id: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    agency_name: Optional[str] = Field(None, description="首次注册时创建租户")


# ==================== 用户 ====================


class UserOut(BaseModel):
    user_id: UUID
    tenant_id: UUID
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 租户 ====================


class TenantOut(BaseModel):
    tenant_id: UUID
    agency_name: str
    subscription_plan: str
    subscription_expiry: Optional[datetime]
    balance_credits: int
    created_at: datetime

    class Config:
        from_attributes = True


class TenantUpdate(BaseModel):
    agency_name: Optional[str] = None
    subscription_plan: Optional[str] = None
    subscription_expiry: Optional[datetime] = None


class CreditTopup(BaseModel):
    credits: int = Field(..., gt=0, description="充值点数")
    remark: Optional[str] = None


# ==================== 境内主体 ====================


class EntityDomesticCreate(BaseModel):
    company_name: str
    uscc: str = Field(..., description="统一社会信用代码")
    industry_code: Optional[str] = None
    net_assets: Optional[float] = None
    net_profit: Optional[float] = None
    legal_representative: Optional[str] = None
    registered_address: Optional[str] = None


class EntityDomesticOut(BaseModel):
    entity_id: UUID
    tenant_id: UUID
    company_name: str
    uscc: str
    industry_code: Optional[str]
    net_assets: Optional[float]
    net_profit: Optional[float]
    legal_representative: Optional[str]
    registered_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class EntityDomesticUpdate(BaseModel):
    company_name: Optional[str] = None
    industry_code: Optional[str] = None
    net_assets: Optional[float] = None
    net_profit: Optional[float] = None
    legal_representative: Optional[str] = None
    registered_address: Optional[str] = None


# ==================== 境外标的 ====================


class EntityOverseasCreate(BaseModel):
    overseas_name_cn: str
    overseas_name_en: Optional[str] = None
    target_country: str
    overseas_industry_code: Optional[str] = None
    registered_capital: Optional[float] = None
    currency: str = "USD"


class EntityOverseasOut(BaseModel):
    entity_id: UUID
    tenant_id: UUID
    overseas_name_cn: str
    overseas_name_en: Optional[str]
    target_country: str
    overseas_industry_code: Optional[str]
    registered_capital: Optional[float]
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True


class EntityOverseasUpdate(BaseModel):
    overseas_name_cn: Optional[str] = None
    overseas_name_en: Optional[str] = None
    target_country: Optional[str] = None
    overseas_industry_code: Optional[str] = None
    registered_capital: Optional[float] = None
    currency: Optional[str] = None


# ==================== 投资项目 ====================


class ProjectStatusLogOut(BaseModel):
    log_id: UUID
    project_id: UUID
    from_status: Optional[str] = None
    to_status: str
    operator_id: Optional[UUID] = None
    remark: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

    @field_validator("from_status", "to_status", mode="before")
    @classmethod
    def enum_to_str(cls, v):
        if hasattr(v, "value"):
            return v.value
        return v


class ProjectCreate(BaseModel):
    domestic_entity_id: Optional[UUID] = None
    overseas_entity_id: Optional[UUID] = None
    project_name: Optional[str] = None
    investment_amount: Optional[float] = None
    currency: str = "USD"
    investment_path: str = "DIRECT"
    funding_source: Optional[dict] = None
    purpose_description: Optional[str] = None


class ProjectOut(BaseModel):
    project_id: UUID
    tenant_id: UUID
    domestic_entity_id: Optional[UUID]
    overseas_entity_id: Optional[UUID]
    project_name: str
    investment_amount: Optional[float]
    currency: str
    investment_path: str
    funding_source: Optional[dict]
    purpose_description: Optional[str]
    status: str
    pre_review_report: Optional[dict]
    feasibility_report: Optional[str]
    due_diligence_report: Optional[str]
    uploaded_files: Optional[list]
    status_logs: Optional[list[ProjectStatusLogOut]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectStatusUpdate(BaseModel):
    target_status: str
    remark: Optional[str] = None
    ndrc_certificate_url: Optional[str] = None
    mofcom_certificate_url: Optional[str] = None


# ==================== 规则引擎 ====================


class RuleCreate(BaseModel):
    rule_type: str
    target_value: str
    risk_level: str
    rule_name: Optional[str] = None
    description: Optional[str] = None
    trigger_action: Optional[dict] = None


class RuleOut(BaseModel):
    rule_id: UUID
    rule_type: str
    target_value: str
    risk_level: str
    rule_name: Optional[str]
    description: Optional[str]
    trigger_action: Optional[dict]
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True


class RuleUpdate(BaseModel):
    rule_type: Optional[str] = None
    target_value: Optional[str] = None
    risk_level: Optional[str] = None
    rule_name: Optional[str] = None
    description: Optional[str] = None
    trigger_action: Optional[dict] = None
    is_active: Optional[int] = None


# ==================== LLM 配置 ====================


class LLMConfigCreate(BaseModel):
    provider_name: str
    display_name: Optional[str] = None
    api_key: str
    base_url: str
    model_version: str
    is_enabled: int = 1
    priority: int = 0
    description: Optional[str] = None


class LLMConfigOut(BaseModel):
    config_id: UUID
    provider_name: str
    display_name: Optional[str]
    base_url: str
    model_version: str
    is_enabled: int
    priority: int
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class LLMConfigUpdate(BaseModel):
    display_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_version: Optional[str] = None
    is_enabled: Optional[int] = None
    priority: Optional[int] = None
    description: Optional[str] = None


# ==================== 计费 ====================


class BillingLogOut(BaseModel):
    transaction_id: UUID
    tenant_id: UUID
    project_id: Optional[UUID]
    billing_type: str
    credits_changed: int
    amount: Optional[float]
    balance_after: int
    remark: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== AI 相关 ====================


class PreReviewRequest(BaseModel):
    project_id: UUID


class PreReviewResponse(BaseModel):
    project_id: UUID
    risk_level: str
    traffic_light: str  # GREEN / YELLOW / RED
    summary: str
    matched_rules: list
    recommendations: list


class ReportGenerateRequest(BaseModel):
    project_id: UUID
    report_type: str = Field(..., description="feasibility / due_diligence")


class ReportGenerateResponse(BaseModel):
    project_id: UUID
    report_type: str
    content: str
    generated_at: datetime


class FinancialExtractRequest(BaseModel):
    project_id: UUID
    file_url: str


class FinancialExtractResponse(BaseModel):
    net_assets: Optional[float]
    net_profit: Optional[float]
    total_revenue: Optional[float]
    extracted_data: dict


# ==================== 通用 ====================


class PageResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ChatAttachment(BaseModel):
    filename: str
    url: str
    content_type: Optional[str] = None


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="对话历史")
    attachments: Optional[List[ChatAttachment]] = Field(
        default=None, description="附件列表"
    )
    context_project_id: Optional[str] = Field(default=None, description="上下文项目ID")
    session_id: Optional[str] = Field(
        default=None, description="会话ID，不传则创建新会话"
    )


class ChatResponse(BaseModel):
    content: str
    intent: str
    confidence: float
    actions: List[Any] = Field(default_factory=list)
    usage: Optional[Any] = None
    session_id: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list)
