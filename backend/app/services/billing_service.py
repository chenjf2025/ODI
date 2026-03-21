"""
计费服务 - 计费鉴权拦截器
"""

from uuid import UUID
from datetime import datetime
from typing import Optional, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.tenant import Tenant, SubscriptionPlan
from app.models.billing import BillingLog, BillingType
from app.utils import utc_now


class BillingService:
    @staticmethod
    def _calculate_credits_from_usage(usage: Dict[str, int]) -> int:
        """根据 LLM token 使用量计算消耗点数 (每1000 tokens = 1点，最少1点)"""
        total = usage.get("total_tokens", 0) if usage else 0
        return max(1, total // 1000)

    @staticmethod
    async def check_and_deduct(
        db: AsyncSession,
        tenant: Tenant,
        project_id: Optional[UUID] = None,
        action_description: str = "项目操作",
        usage: Optional[Dict[str, int]] = None,
    ) -> bool:
        """
        计费鉴权拦截器:
        - ANNUAL 且在有效期内 -> 直接放行
        - FREE / 非年费 -> 检查余额足够，扣减实际消耗点数
        - usage 参数传入时，根据实际 token 量计算点数（每1000 tokens = 1点）
        """
        now = utc_now()
        credits_to_deduct = (
            BillingService._calculate_credits_from_usage(usage) if usage else 1
        )

        # 年费会员在有效期内，直接放行
        if (
            tenant.subscription_plan == SubscriptionPlan.ANNUAL
            and tenant.subscription_expiry
            and tenant.subscription_expiry > now
        ):
            # 记录 0 消耗日志
            log = BillingLog(
                tenant_id=tenant.tenant_id,
                project_id=project_id,
                billing_type=BillingType.PROJECT_DEDUCTION,
                credits_changed=0,
                amount=0,
                balance_after=tenant.balance_credits,
                prompt_tokens=usage.get("prompt_tokens") if usage else None,
                completion_tokens=usage.get("completion_tokens") if usage else None,
                total_tokens=usage.get("total_tokens") if usage else None,
                remark=f"{action_description} (年费会员免扣)",
            )
            db.add(log)
            await db.flush()
            return True

        # 非年费会员 - 检查余额
        if tenant.balance_credits < credits_to_deduct:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "INSUFFICIENT_FUNDS",
                    "message": "点数余额不足，请充值后再操作",
                    "current_balance": tenant.balance_credits,
                    "required": credits_to_deduct,
                },
            )

        # 扣减对应点数
        tenant.balance_credits -= credits_to_deduct
        log = BillingLog(
            tenant_id=tenant.tenant_id,
            project_id=project_id,
            billing_type=BillingType.PROJECT_DEDUCTION,
            credits_changed=-credits_to_deduct,
            amount=0,
            balance_after=tenant.balance_credits,
            prompt_tokens=usage.get("prompt_tokens") if usage else None,
            completion_tokens=usage.get("completion_tokens") if usage else None,
            total_tokens=usage.get("total_tokens") if usage else None,
            remark=action_description,
        )
        db.add(log)
        await db.flush()
        return True

    @staticmethod
    async def topup_credits(
        db: AsyncSession,
        tenant: Tenant,
        credits: int,
        remark: str = "点数充值",
    ) -> Tenant:
        """充值点数"""
        tenant.balance_credits += credits
        log = BillingLog(
            tenant_id=tenant.tenant_id,
            billing_type=BillingType.CREDIT_TOPUP,
            credits_changed=credits,
            amount=0,
            balance_after=tenant.balance_credits,
            remark=remark,
        )
        db.add(log)
        await db.flush()
        return tenant

    @staticmethod
    async def renew_annual(
        db: AsyncSession,
        tenant: Tenant,
        expiry: datetime,
        amount: float = 0,
    ) -> Tenant:
        """年费续费"""
        tenant.subscription_plan = SubscriptionPlan.ANNUAL
        tenant.subscription_expiry = expiry
        log = BillingLog(
            tenant_id=tenant.tenant_id,
            billing_type=BillingType.ANNUAL_RENEWAL,
            credits_changed=0,
            amount=amount,
            balance_after=tenant.balance_credits,
            remark=f"年费续费至 {expiry.strftime('%Y-%m-%d')}",
        )
        db.add(log)
        await db.flush()
        return tenant
