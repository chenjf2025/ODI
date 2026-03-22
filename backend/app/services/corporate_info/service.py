"""
企业征信主服务 - 含降级切换逻辑
"""

from typing import Optional, List
import logging

from app.config import settings
from app.exceptions import CorporateInfoError
from app.services.corporate_info.base import CorporateInfoProvider, DomesticCompanyDTO
from app.services.corporate_info.qichacha import QiChaChaProvider
from app.services.corporate_info.tianyancha import TianYanChaProvider
from app.services.corporate_info.baidu import BaiduCreditProvider

logger = logging.getLogger(__name__)


class CorporateInfoService:
    """
    企业征信统一服务
    - 支持动态切换默认数据源
    - 主调用 API 失败时自动降级到备用数据源
    """

    def __init__(self):
        self._providers: dict[str, CorporateInfoProvider] = {}
        self._default_provider: str = settings.DEFAULT_CORP_INFO_PROVIDER
        self._initialize_providers()

    def _initialize_providers(self):
        """初始化所有数据源"""
        if settings.QICHACCHA_API_KEY:
            self._providers["qichacha"] = QiChaChaProvider(settings.QICHACHA_API_KEY)
        if settings.TIANYANCHA_API_KEY:
            self._providers["tianyancha"] = TianYanChaProvider(
                settings.TIANYANCHA_API_KEY
            )
        if settings.BAIDU_CREDIT_API_KEY:
            self._providers["baidu"] = BaiduCreditProvider(
                settings.BAIDU_CREDIT_API_KEY
            )

    def set_default_provider(self, provider_name: str):
        if provider_name not in self._providers:
            raise ValueError(f"未注册的数据源: {provider_name}")
        self._default_provider = provider_name

    async def search_company(self, keyword: str) -> List[DomesticCompanyDTO]:
        """搜索企业 - 含降级逻辑"""
        providers = self._get_ordered_providers()
        failed_providers = []
        for provider in providers:
            try:
                results = await provider.search_company(keyword)
                if results:
                    logger.info(f"企业搜索成功 [provider={provider.provider_name}]")
                    return results
            except Exception as e:
                logger.warning(
                    f"数据源 {provider.provider_name} 搜索失败: {type(e).__name__}: {str(e)}"
                )
                failed_providers.append(f"{provider.provider_name}({type(e).__name__})")
                continue
        raise CorporateInfoError(
            message=f"所有企业征信数据源均查询失败（关键词: {keyword}）",
            providers=[p.provider_name for p in providers],
            last_error=f"失败数据源: {', '.join(failed_providers) if failed_providers else '无'}",
        )

    async def get_company_detail(self, uscc: str) -> Optional[DomesticCompanyDTO]:
        """获取企业详情 - 含降级逻辑"""
        providers = self._get_ordered_providers()
        failed_providers = []
        for provider in providers:
            try:
                result = await provider.get_company_detail(uscc)
                if result:
                    logger.info(f"企业详情获取成功 [provider={provider.provider_name}]")
                    return result
            except Exception as e:
                logger.warning(
                    f"数据源 {provider.provider_name} 获取详情失败: {type(e).__name__}: {str(e)}"
                )
                failed_providers.append(f"{provider.provider_name}({type(e).__name__})")
                continue
        raise CorporateInfoError(
            message=f"所有企业征信数据源均查询失败（统一社会信用代码: {uscc}）",
            providers=[p.provider_name for p in providers],
            last_error=f"失败数据源: {', '.join(failed_providers) if failed_providers else '无'}",
        )

    def _get_ordered_providers(self) -> List[CorporateInfoProvider]:
        """按优先级排列提供商：默认提供商优先"""
        ordered = []
        if self._default_provider in self._providers:
            ordered.append(self._providers[self._default_provider])
        for name, provider in self._providers.items():
            if name != self._default_provider:
                ordered.append(provider)
        return ordered


# 全局实例
corporate_info_service = CorporateInfoService()
