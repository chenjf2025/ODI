"""
规则引擎服务 - 国家/行业规则匹配
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rules import RulesEngine, RuleType, RiskLevel
from app.utils import enum_value


class RulesService:
    @staticmethod
    async def match_rules(
        db: AsyncSession,
        target_country: Optional[str] = None,
        industry_code: Optional[str] = None,
    ) -> dict:
        """
        根据国家和行业匹配规则引擎，返回风险等级和触发动作
        """
        matched_rules = []
        overall_risk = RiskLevel.LOW

        # 匹配国家规则
        if target_country:
            result = await db.execute(
                select(RulesEngine).where(
                    RulesEngine.rule_type == RuleType.COUNTRY,
                    RulesEngine.target_value == target_country,
                    RulesEngine.is_active == 1,
                )
            )
            country_rules = result.scalars().all()
            for rule in country_rules:
                matched_rules.append(
                    {
                        "rule_id": str(rule.rule_id),
                        "rule_type": enum_value(rule.rule_type),
                        "target_value": rule.target_value,
                        "risk_level": enum_value(rule.risk_level),
                        "rule_name": rule.rule_name,
                        "description": rule.description,
                        "trigger_action": rule.trigger_action,
                    }
                )
                if _risk_higher(rule.risk_level, overall_risk):
                    overall_risk = rule.risk_level

        # 匹配行业规则
        if industry_code:
            result = await db.execute(
                select(RulesEngine).where(
                    RulesEngine.rule_type == RuleType.INDUSTRY,
                    RulesEngine.target_value == industry_code,
                    RulesEngine.is_active == 1,
                )
            )
            industry_rules = result.scalars().all()
            for rule in industry_rules:
                matched_rules.append(
                    {
                        "rule_id": str(rule.rule_id),
                        "rule_type": enum_value(rule.rule_type),
                        "target_value": rule.target_value,
                        "risk_level": enum_value(rule.risk_level),
                        "rule_name": rule.rule_name,
                        "description": rule.description,
                        "trigger_action": rule.trigger_action,
                    }
                )
                if _risk_higher(rule.risk_level, overall_risk):
                    overall_risk = rule.risk_level

        # 确定红绿灯
        risk_val = enum_value(overall_risk)
        traffic_light = {
            "HIGH": "RED",
            "MEDIUM": "YELLOW",
            "LOW": "GREEN",
        }.get(risk_val, "GREEN")

        return {
            "overall_risk": risk_val,
            "traffic_light": traffic_light,
            "matched_rules": matched_rules,
            "total_matched": len(matched_rules),
        }

    @staticmethod
    async def get_all_rules(
        db: AsyncSession,
        rule_type: Optional[str] = None,
        is_active: Optional[int] = None,
    ) -> List[RulesEngine]:
        query = select(RulesEngine)
        if rule_type:
            query = query.where(RulesEngine.rule_type == rule_type)
        if is_active is not None:
            query = query.where(RulesEngine.is_active == is_active)
        result = await db.execute(query.order_by(RulesEngine.created_at.desc()))
        return result.scalars().all()


def _risk_higher(new_risk, current_risk) -> bool:
    """比较风险等级（支持 enum 和 string 两种输入）"""
    level_map = {
        RiskLevel.LOW: 0,
        RiskLevel.MEDIUM: 1,
        RiskLevel.HIGH: 2,
        "LOW": 0,
        "MEDIUM": 1,
        "HIGH": 2,
    }
    return level_map.get(enum_value(new_risk), 0) > level_map.get(
        enum_value(current_risk), 0
    )
