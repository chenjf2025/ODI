"""
企查查适配器
"""
from typing import Optional
import httpx
from app.services.corporate_info.base import CorporateInfoProvider, DomesticCompanyDTO


class QiChaChaProvider(CorporateInfoProvider):
    """企查查 API 适配器"""

    BASE_URL = "https://api.qichacha.com"

    @property
    def provider_name(self) -> str:
        return "qichacha"

    async def search_company(self, keyword: str) -> list[DomesticCompanyDTO]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/open/search",
                    params={"keyword": keyword},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                response.raise_for_status()
                data = response.json()

            results = []
            for item in data.get("data", {}).get("items", []):
                results.append(DomesticCompanyDTO(
                    company_name=item.get("name", ""),
                    uscc=item.get("creditCode", ""),
                    legal_representative=item.get("legalPerson", ""),
                    registered_capital=item.get("registeredCapital", ""),
                    company_status=item.get("status", ""),
                    registered_address=item.get("address", ""),
                ))
            return results
        except Exception:
            return []

    async def get_company_detail(self, uscc: str) -> Optional[DomesticCompanyDTO]:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.BASE_URL}/open/detail",
                    params={"creditCode": uscc},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                response.raise_for_status()
                data = response.json().get("data", {})

            return DomesticCompanyDTO(
                company_name=data.get("name", ""),
                uscc=data.get("creditCode", ""),
                legal_representative=data.get("legalPerson", ""),
                registered_capital=data.get("registeredCapital", ""),
                establishment_date=data.get("establishDate", ""),
                company_status=data.get("status", ""),
                registered_address=data.get("address", ""),
                business_scope=data.get("businessScope", ""),
                industry_code=data.get("industryCode", ""),
                company_type=data.get("companyType", ""),
            )
        except Exception:
            return None

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.BASE_URL}/health")
                return response.status_code == 200
        except Exception:
            return False
