"""数据字典初始数据种子脚本"""

import uuid
from datetime import datetime
from sqlalchemy import select
from app.database import AsyncSessionLocal, engine
from app.models.data_dictionary import DataDictionary
from app.models.tenant import Tenant


SEED_DATA = {
    "investment_path": [
        {"label": "直接投资", "value": "DIRECT", "sort": 1},
        {"label": "香港 SPV", "value": "SPV_HK", "sort": 2},
        {"label": "新加坡 SPV", "value": "SPV_SGP", "sort": 3},
        {"label": "多层架构", "value": "MULTI_LAYER", "sort": 4},
    ],
    "currency": [
        {"label": "美元", "value": "USD", "sort": 1},
        {"label": "人民币", "value": "CNY", "sort": 2},
        {"label": "港币", "value": "HKD", "sort": 3},
        {"label": "欧元", "value": "EUR", "sort": 4},
        {"label": "英镑", "value": "GBP", "sort": 5},
        {"label": "日元", "value": "JPY", "sort": 6},
        {"label": "新加坡元", "value": "SGD", "sort": 7},
    ],
    "declaration_target": [
        {"label": "发改委", "value": "NDRC", "sort": 1},
        {"label": "商务部", "value": "MOFCOM", "sort": 2},
        {"label": "外汇局", "value": "SAFE", "sort": 3},
    ],
    "approval_status": [
        {"label": "待审批", "value": "PENDING", "sort": 1},
        {"label": "已通过", "value": "APPROVED", "sort": 2},
        {"label": "已驳回", "value": "REJECTED", "sort": 3},
        {"label": "已撤回", "value": "WITHDRAWN", "sort": 4},
    ],
    "approval_level": [
        {"label": "一级审批", "value": "FIRST", "sort": 1},
        {"label": "复核", "value": "REVIEW", "sort": 2},
        {"label": "终审", "value": "FINAL", "sort": 3},
    ],
    "remittance_status": [
        {"label": "待汇出", "value": "PENDING", "sort": 1},
        {"label": "已汇出", "value": "REMITTED", "sort": 2},
        {"label": "已撤销", "value": "CANCELLED", "sort": 3},
    ],
    "declaration_status": [
        {"label": "待提交", "value": "PENDING", "sort": 1},
        {"label": "审核中", "value": "IN_PROGRESS", "sort": 2},
        {"label": "已通过", "value": "APPROVED", "sort": 3},
        {"label": "已驳回", "value": "REJECTED", "sort": 4},
    ],
    "sensitive_level": [
        {"label": "低风险", "value": "LOW", "sort": 1},
        {"label": "中风险", "value": "MEDIUM", "sort": 2},
        {"label": "高风险", "value": "HIGH", "sort": 3},
        {"label": "禁止", "value": "FORBIDDEN", "sort": 4},
    ],
    "project_status": [
        {"label": "智能预审", "value": "PRE_REVIEW", "sort": 1},
        {"label": "材料准备", "value": "DATA_COLLECTION", "sort": 2},
        {"label": "发改委备案", "value": "NDRC_FILING_PENDING", "sort": 3},
        {"label": "发改委通过", "value": "NDRC_APPROVED", "sort": 4},
        {"label": "商务部备案", "value": "MOFCOM_FILING_PENDING", "sort": 5},
        {"label": "商务部通过", "value": "MOFCOM_APPROVED", "sort": 6},
        {"label": "银行登记", "value": "BANK_REG_PENDING", "sort": 7},
        {"label": "资金汇出", "value": "FUNDS_REMITTED", "sort": 8},
        {"label": "投后管理", "value": "POST_INVESTMENT", "sort": 9},
    ],
    "target_country": [
        {"label": "香港", "value": "HK", "sort": 1},
        {"label": "新加坡", "value": "SG", "sort": 2},
        {"label": "美国", "value": "US", "sort": 3},
        {"label": "英国", "value": "GB", "sort": 4},
        {"label": "德国", "value": "DE", "sort": 5},
        {"label": "日本", "value": "JP", "sort": 6},
        {"label": "韩国", "value": "KR", "sort": 7},
        {"label": "澳大利亚", "value": "AU", "sort": 8},
        {"label": "加拿大", "value": "CA", "sort": 9},
        {"label": "荷兰", "value": "NL", "sort": 10},
        {"label": "开曼群岛", "value": "KY", "sort": 11},
        {"label": "英属维尔京群岛", "value": "VG", "sort": 12},
    ],
    "industry_code": [
        {"label": "制造业", "value": "C", "sort": 1},
        {"label": "信息技术", "value": "I", "sort": 2},
        {"label": "金融服务", "value": "J", "sort": 3},
        {"label": "批发零售", "value": "F", "sort": 4},
        {"label": "房地产", "value": "K", "sort": 5},
        {"label": "租赁和商务服务", "value": "L", "sort": 6},
        {"label": "科学研究和技术服务", "value": "M", "sort": 7},
        {"label": "交通运输", "value": "G", "sort": 8},
        {"label": "文化体育娱乐", "value": "R", "sort": 9},
        {"label": "教育", "value": "P", "sort": 10},
        {"label": "卫生和社会工作", "value": "Q", "sort": 11},
        {"label": "水利环境和公共设施", "value": "N", "sort": 12},
        {"label": "农林牧渔", "value": "A", "sort": 13},
        {"label": "采矿业", "value": "B", "sort": 14},
        {"label": "电力热力燃气", "value": "D", "sort": 15},
        {"label": "建筑业", "value": "E", "sort": 16},
        {"label": "住宿和餐饮", "value": "H", "sort": 17},
        {"label": "居民服务修理", "value": "O", "sort": 18},
    ],
}


async def seed_dictionary():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Tenant))
        tenants = result.scalars().all()

        if not tenants:
            print("No tenants found, skipping seed")
            return

        for tenant in tenants:
            tenant_id = tenant.tenant_id

            for dict_type, items in SEED_DATA.items():
                for item in items:
                    result = await session.execute(
                        select(DataDictionary).where(
                            DataDictionary.tenant_id == tenant_id,
                            DataDictionary.dict_type == dict_type,
                            DataDictionary.dict_value == item["value"],
                        )
                    )
                    existing = result.scalar_one_or_none()
                    if not existing:
                        dic = DataDictionary(
                            dict_id=uuid.uuid4(),
                            tenant_id=tenant_id,
                            dict_type=dict_type,
                            dict_label=item["label"],
                            dict_value=item["value"],
                            sort_order=item["sort"],
                            is_active=1,
                            created_at=datetime.now(),
                        )
                        session.add(dic)

            await session.commit()
            print(f"Seeded dictionaries for tenant: {tenant.agency_name}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(seed_dictionary())
