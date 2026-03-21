"""
百度企业信用适配器
"""
from typing import Optional
import httpx
from app.services.corporate_info.base import CorporateInfoProvider, DomesticCompanyDTO


class BaiduCreditProvider(CorporateInfoProvider):
    """百度企业信用 API 适配器"""

    BASE_URL = "https://aip.baidubce.com/rest/2.0/business"

    @property
    def provider_name(self) -> str:
        return "baidu"

    async def search_company(self, keyword: str) -> list[DomesticCompanyDTO]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/search",
                    params={"keyword": keyword, "access_token": self.api_key},
                )
                response.raise_for_status()
                data = response.json()

            results = []
            for item in data.get("data", []):
                results.append(DomesticCompanyDTO(
                    company_name=item.get("entName", ""),
                    uscc=item.get("creditNo", ""),
                    legal_representative=item.get("legalPerson", ""),
                    registered_capital=item.get("regCapital", ""),
                    company_status=item.get("openStatus", ""),
                ))
            return results
        except Exception:
            return []

    async def get_company_detail(self, uscc: str) -> Optional[DomesticCompanyDTO]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/detail",
                    params={"creditNo": uscc, "access_token": self.api_key},
                )
                response.raise_for_status()
                data = response.json().get("data", {})

            return DomesticCompanyDTO(
                company_name=data.get("entName", ""),
                uscc=data.get("creditNo", ""),
                legal_representative=data.get("legalPerson", ""),
                registered_capital=data.get("regCapital", ""),
                establishment_date=data.get("startDate", ""),
                company_status=data.get("openStatus", ""),
                registered_address=data.get("address", ""),
                business_scope=data.get("scope", ""),
            )
        except Exception:
            return None

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/health",
                    params={"access_token": self.api_key},
                )
                return response.status_code == 200
        except Exception:
            return False
