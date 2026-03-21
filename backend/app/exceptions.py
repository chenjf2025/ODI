"""
业务异常定义 - 替代裸 except Exception
"""


class ODIBaseError(Exception):
    """业务异常基类"""

    def __init__(self, message: str, code: str = "ODI_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class LLMAPIError(ODIBaseError):
    """LLM API 调用失败（所有提供商均不可用或响应异常）"""

    def __init__(self, message: str, providers: list[str] = None, last_error: str = ""):
        self.providers = providers or []
        self.last_error = last_error
        detail = f"{message}"
        if providers:
            detail += f" (尝试的提供商: {', '.join(providers)})"
        if last_error:
            detail += f" | 最后错误: {last_error}"
        super().__init__(detail, code="LLM_API_ERROR")


class CorporateInfoError(ODIBaseError):
    """企业征信查询失败（所有数据源均不可用）"""

    def __init__(self, message: str, providers: list[str] = None, last_error: str = ""):
        self.providers = providers or []
        self.last_error = last_error
        detail = f"{message}"
        if providers:
            detail += f" (尝试的数据源: {', '.join(providers)})"
        if last_error:
            detail += f" | 最后错误: {last_error}"
        super().__init__(detail, code="CORPORATE_INFO_ERROR")


class BillingError(ODIBaseError):
    """计费相关错误（余额不足等）"""

    def __init__(self, message: str, current_balance: int = None):
        self.current_balance = current_balance
        detail = message
        if current_balance is not None:
            detail += f" (当前余额: {current_balance})"
        super().__init__(detail, code="BILLING_ERROR")


class ProjectStateError(ODIBaseError):
    """项目状态流转错误（非法状态转移）"""

    def __init__(
        self, message: str, current_status: str = None, target_status: str = None
    ):
        self.current_status = current_status
        self.target_status = target_status
        detail = message
        if current_status and target_status:
            detail += f" ({current_status} → {target_status})"
        super().__init__(detail, code="PROJECT_STATE_ERROR")
