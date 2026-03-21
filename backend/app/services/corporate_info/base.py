"""
企业征信数据源 - 基类定义（适配器/策略模式）
"""
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class DomesticCompanyDTO:
    """统一的企业信息内部数据结构"""
    company_name: str = ""
    uscc: str = ""                          # 统一社会信用代码
    legal_representative: str = ""
    registered_capital: str = ""
    establishment_date: str = ""
    company_status: str = ""
    registered_address: str = ""
    business_scope: str = ""
    industry_code: str = ""
    company_type: str = ""
    approval_date: str = ""
    extra_data: dict = field(default_factory=dict)


class CorporateInfoProvider(ABC):
    """企业征信数据源提供商基类"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def search_company(self, keyword: str) -> list[DomesticCompanyDTO]:
        """根据关键词搜索企业"""
        pass

    @abstractmethod
    async def get_company_detail(self, uscc: str) -> Optional[DomesticCompanyDTO]:
        """根据统一信用代码获取企业详情"""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """检查服务可用性"""
        pass
