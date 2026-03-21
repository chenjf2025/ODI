"""
通用工具函数
"""

from datetime import datetime, timezone
from typing import Any, Union


def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime (Python 3.12+ compatible).

    Replaces deprecated datetime.utcnow() which produces naive datetimes and
    triggers DeprecationWarning in Python 3.12+.
    """
    return datetime.now(timezone.utc)


def enum_value(e: Union[Any, str]) -> str:
    """Normalize an enum value to its string representation.

    Handles both:
      - Python enum members (e.g., RiskLevel.HIGH) → returns "HIGH"
      - Already-plain strings (e.g., "HIGH") → returns "HIGH" as-is

    This avoids inconsistent patterns like:
      - rule.risk_level.value  (when enum)
      - rule.risk_level        (when already string)
    """
    if isinstance(e, str):
        return e
    if hasattr(e, "value"):
        return e.value
    return str(e)
