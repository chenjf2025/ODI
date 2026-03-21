"""
天眼查适配器
"""
from typing import Optional
import httpx
from app.services.corporate_info.base import CorporateInfoProvider, DomesticCompanyDTO


class TianYanChaProvider(CorporateInfoProvider):
    """天眼查 API 适配器"""

    BASE_URL = "https://open.api.tianyancha.com"

    @property
    def provider_name(self) -> str:
        return "tianyancha"

    async def search_company(self, keyword: str) -> list[DomesticCompanyDTO]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/services/open/search",
                    params={"word": keyword},
                    headers={"Authorization": self.api_key},
                )
                response.raise_for_status()
                data = response.json()

            results = []
            for item in data.get("result", {}).get("items", []):
                results.append(DomesticCompanyDTO(
                    company_name=item.get("name", ""),
                    uscc=item.get("creditCode", ""),
                    legal_representative=item.get("legalPersonName", ""),
                    registered_capital=item.get("regCapital", ""),
                    company_status=item.get("regStatus", ""),
                ))
            return results
        except Exception:
            return []

    async def get_company_detail(self, uscc: str) -> Optional[DomesticCompanyDTO]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/services/open/ic/baseinfo",
                    params={"keyword": uscc},
                    headers={"Authorization": self.api_key},
                )
                response.raise_for_status()
                data = response.json().get("result", {})

            return DomesticCompanyDTO(
                company_name=data.get("name", ""),
                uscc=data.get("creditCode", ""),
                legal_representative=data.get("legalPersonName", ""),
                registered_capital=data.get("regCapital", ""),
                establishment_date=data.get("estiblishTime", ""),
                company_status=data.get("regStatus", ""),
                registered_address=data.get("regLocation", ""),
                business_scope=data.get("businessScope", ""),
                industry_code=data.get("industryAll", {}).get("code", ""),
                company_type=data.get("companyOrgType", ""),
            )
        except Exception:
            return None

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/health",
                    headers={"Authorization": self.api_key},
                )
                return response.status_code == 200
        except Exception:
            return False
