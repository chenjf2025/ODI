"""
智能 ODI 合规与出海服务管控 SaaS 平台 - 主入口
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import engine, Base, AsyncSessionLocal
from app.services.llm.gateway import llm_gateway
from app.services.llm.providers.deepseek import DeepSeekProvider
from app.services.llm.providers.kimi import KimiProvider
from app.services.llm.providers.minimax import MiniMaxProvider
from app.models.llm_config import LLMConfig

limiter = Limiter(key_func=get_remote_address)

# API 路由
from app.api.auth import router as auth_router
from app.api.projects import router as projects_router
from app.api.entities import router as entities_router
from app.api.ai import router as ai_router
from app.api.rules import router as rules_router
from app.api.tenants import router as tenants_router
from app.api.admin import router as admin_router
from app.api.admin_export import router as admin_export_router
from app.api.export import router as export_router
from app.api.upload import router as upload_router
from app.api.departments import router as departments_router
from app.api.dictionaries import router as dictionaries_router
from app.api.approvals import router as approvals_router
from app.api.remittances import router as remittances_router
from app.api.declarations import router as declarations_router
from app.api.logs import router as logs_router
from app.api.sensitive_words import router as sensitive_words_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 提供商名称 -> Provider 类的映射
PROVIDER_CLASS_MAP = {
    "deepseek": DeepSeekProvider,
    "kimi": KimiProvider,
    "minimax": MiniMaxProvider,
}

# 提供商默认模型版本
DEFAULT_MODELS = {
    "deepseek": "deepseek-chat",
    "kimi": "moonshot-v1-128k",
    "minimax": "abab6.5s-chat",
}


async def _seed_export_templates():
    """初始化导出字段模板数据（仅在表为空时）"""
    from app.models.export_template import ExportTemplate, TemplateType

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ExportTemplate))
            if result.scalar_one_or_none() is not None:
                logger.info("导出模板已有数据，跳过 seed")
                return

            ndrc_templates = [
                {
                    "column_index": 1,
                    "xml_tag": "ProjectName",
                    "display_name": "项目名称",
                    "data_key": "project_name",
                },
                {
                    "column_index": 2,
                    "xml_tag": "InvestorName",
                    "display_name": "投资方名称",
                    "data_key": "company_name",
                },
                {
                    "column_index": 3,
                    "xml_tag": "CreditCode",
                    "display_name": "统一社会信用代码",
                    "data_key": "uscc",
                },
                {
                    "column_index": 4,
                    "xml_tag": "TargetCountry",
                    "display_name": "目的国",
                    "data_key": "target_country",
                },
                {
                    "column_index": 5,
                    "xml_tag": "OverseasCompanyNameCN",
                    "display_name": "境外企业名称(中文)",
                    "data_key": "overseas_name_cn",
                },
                {
                    "column_index": 6,
                    "xml_tag": "OverseasCompanyNameEN",
                    "display_name": "境外企业名称(英文)",
                    "data_key": "overseas_name_en",
                },
                {
                    "column_index": 7,
                    "xml_tag": "InvestmentAmount",
                    "display_name": "投资金额",
                    "data_key": "investment_amount",
                },
                {
                    "column_index": 8,
                    "xml_tag": "Currency",
                    "display_name": "币种",
                    "data_key": "currency",
                },
                {
                    "column_index": 9,
                    "xml_tag": "InvestmentPath",
                    "display_name": "投资路径",
                    "data_key": "investment_path",
                },
                {
                    "column_index": 10,
                    "xml_tag": "IndustryCode",
                    "display_name": "境内行业代码",
                    "data_key": "industry_code",
                },
                {
                    "column_index": 11,
                    "xml_tag": "OverseasIndustryCode",
                    "display_name": "境外行业代码",
                    "data_key": "overseas_industry_code",
                },
                {
                    "column_index": 12,
                    "xml_tag": "NetAssets",
                    "display_name": "净资产",
                    "data_key": "net_assets",
                },
                {
                    "column_index": 13,
                    "xml_tag": "NetProfit",
                    "display_name": "净利润",
                    "data_key": "net_profit",
                },
            ]
            mofcom_templates = [
                {
                    "column_index": 1,
                    "xml_tag": None,
                    "display_name": "项目名称",
                    "data_key": "project_name",
                },
                {
                    "column_index": 2,
                    "xml_tag": None,
                    "display_name": "境内投资主体",
                    "data_key": "company_name",
                },
                {
                    "column_index": 3,
                    "xml_tag": None,
                    "display_name": "统一社会信用代码",
                    "data_key": "uscc",
                },
                {
                    "column_index": 4,
                    "xml_tag": None,
                    "display_name": "投资目的国/地区",
                    "data_key": "target_country",
                },
                {
                    "column_index": 5,
                    "xml_tag": None,
                    "display_name": "境外企业名称(中文)",
                    "data_key": "overseas_name_cn",
                },
                {
                    "column_index": 6,
                    "xml_tag": None,
                    "display_name": "境外企业名称(英文)",
                    "data_key": "overseas_name_en",
                },
                {
                    "column_index": 7,
                    "xml_tag": None,
                    "display_name": "拟投资总额",
                    "data_key": "investment_amount",
                },
                {
                    "column_index": 8,
                    "xml_tag": None,
                    "display_name": "币种",
                    "data_key": "currency",
                },
                {
                    "column_index": 9,
                    "xml_tag": None,
                    "display_name": "投资路径",
                    "data_key": "investment_path",
                },
                {
                    "column_index": 10,
                    "xml_tag": None,
                    "display_name": "境内行业代码",
                    "data_key": "industry_code",
                },
                {
                    "column_index": 11,
                    "xml_tag": None,
                    "display_name": "境外行业代码",
                    "data_key": "overseas_industry_code",
                },
                {
                    "column_index": 12,
                    "xml_tag": None,
                    "display_name": "注册资本",
                    "data_key": "registered_capital",
                },
                {
                    "column_index": 13,
                    "xml_tag": None,
                    "display_name": "最近一年净资产",
                    "data_key": "net_assets",
                },
                {
                    "column_index": 14,
                    "xml_tag": None,
                    "display_name": "最近一年净利润",
                    "data_key": "net_profit",
                },
                {
                    "column_index": 15,
                    "xml_tag": None,
                    "display_name": "投资必要性说明",
                    "data_key": "purpose_description",
                },
            ]

            for t in ndrc_templates:
                session.add(ExportTemplate(template_type=TemplateType.NDRC, **t))
            for t in mofcom_templates:
                session.add(ExportTemplate(template_type=TemplateType.MOFCOM, **t))
            await session.commit()
            logger.info(
                f"导出模板 seed 完成: {len(ndrc_templates)} NDRC + {len(mofcom_templates)} MOFCOM"
            )
    except Exception as e:
        logger.warning(f"导出模板 seed 失败: {e}")


DICT_SEED_DATA = {
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


async def _seed_dictionaries():
    from app.models.data_dictionary import DataDictionary
    from app.models.tenant import Tenant

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Tenant))
            tenants = result.scalars().all()
            if not tenants:
                logger.info("No tenants found, skipping dictionary seed")
                return

            total_seeded = 0
            for tenant in tenants:
                tenant_id = tenant.tenant_id
                for dict_type, items in DICT_SEED_DATA.items():
                    for item in items:
                        result = await session.execute(
                            select(DataDictionary).where(
                                DataDictionary.tenant_id == tenant_id,
                                DataDictionary.dict_type == dict_type,
                                DataDictionary.dict_value == item["value"],
                            )
                        )
                        if result.scalar_one_or_none() is None:
                            dic = DataDictionary(
                                tenant_id=tenant_id,
                                dict_type=dict_type,
                                dict_label=item["label"],
                                dict_value=item["value"],
                                sort_order=item["sort"],
                                is_active=1,
                            )
                            session.add(dic)
                            total_seeded += 1
                await session.commit()
            logger.info(f"字典数据 seed 完成: {total_seeded} 条")
    except Exception as e:
        logger.warning(f"字典数据 seed 失败: {e}")


async def reload_llm_providers_from_db():
    """
    从数据库 llm_configs 表加载 LLM 提供商配置。
    管理员在界面修改配置后调用此函数即可热更新。
    """
    loaded_count = 0
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(LLMConfig)
                .where(LLMConfig.is_enabled == 1)
                .order_by(LLMConfig.priority)
            )
            configs = result.scalars().all()

        for cfg in configs:
            provider_cls = PROVIDER_CLASS_MAP.get(cfg.provider_name)
            if not provider_cls:
                logger.warning(f"未知的提供商类型: {cfg.provider_name}，跳过")
                continue
            provider = provider_cls(
                api_key=cfg.api_key,
                base_url=cfg.base_url,
                model=cfg.model_version,
            )
            llm_gateway.register_provider(cfg.provider_name, provider)
            logger.info(
                f"✅ 从数据库加载 LLM 提供商: {cfg.provider_name} (模型: {cfg.model_version})"
            )
            loaded_count += 1

    except Exception as e:
        logger.warning(f"从数据库加载 LLM 配置失败: {e}")

    return loaded_count


def _init_llm_providers_from_env():
    """从环境变量初始化 LLM 提供商（作为后备方案）"""
    count = 0
    env_configs = [
        ("deepseek", settings.DEEPSEEK_API_KEY, settings.DEEPSEEK_BASE_URL),
        ("kimi", settings.KIMI_API_KEY, settings.KIMI_BASE_URL),
        ("minimax", settings.MINIMAX_API_KEY, settings.MINIMAX_BASE_URL),
    ]
    for name, api_key, base_url in env_configs:
        # 跳过占位符 key 和已从 DB 加载的提供商
        if (
            not api_key
            or api_key.startswith("sk-dev-")
            or api_key.endswith("-placeholder")
        ):
            continue
        if llm_gateway.get_provider(name):
            continue  # 已从 DB 加载，不覆盖

        # 自动检测模型：如果 base_url 指向其他提供商，使用对应的模型名
        model = DEFAULT_MODELS[name]
        if "deepseek" in (base_url or ""):
            model = "deepseek-chat"
        elif "moonshot" in (base_url or ""):
            model = "moonshot-v1-128k"
        elif "minimax" in (base_url or ""):
            model = "abab6.5s-chat"

        provider_cls = PROVIDER_CLASS_MAP[name]
        provider = provider_cls(
            api_key=api_key,
            base_url=base_url,
            model=model,
        )
        llm_gateway.register_provider(name, provider)
        logger.info(
            f"✅ 从环境变量加载 LLM 提供商: {name} (base_url={base_url}, model={model})"
        )
        count += 1
    return count


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 ODI SaaS 平台启动中...")

    # 使用 Alembic 执行数据库迁移
    try:
        import alembic.config
        import alembic.command
        import os

        alembic_cfg = alembic.config.Config(
            os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
        )
        # 在线程池中同步运行 alembic（因为 alembic 内部是同步的）
        import asyncio

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, alembic.command.upgrade, alembic_cfg, "head")
        logger.info("✅ 数据库迁移完成")
    except Exception as e:
        logger.warning(f"⚠️  数据库迁移失败，将尝试 create_all: {e}")
        # 回退到 create_all（仅开发模式）
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ 数据库表已同步 (create_all 回退)")

    # 优先从数据库加载 LLM 配置
    db_count = await reload_llm_providers_from_db()
    # 环境变量作为后备
    env_count = _init_llm_providers_from_env()
    total = len(llm_gateway.list_providers())
    logger.info(
        f"✅ LLM 提供商加载完成: {total} 个 (数据库: {db_count}, 环境变量: {env_count})"
    )

    if total == 0:
        logger.warning(
            "⚠️  没有可用的 LLM 提供商！请在管理后台 > 系统配置中添加，或在 .env 文件中配置 API Key"
        )

    # 初始化导出字段模板（seed data）
    await _seed_export_templates()

    # 初始化数据字典（seed data）
    await _seed_dictionaries()

    yield

    logger.info("🛑 ODI SaaS 平台关闭")
    await engine.dispose()


# 创建 FastAPI 应用
app = FastAPI(
    title="智能 ODI 合规与出海服务管控 SaaS 平台",
    description="面向跨境出海企业的智能 ODI 备案 SaaS 平台，支持智能预审、AI 报告生成、多部委表单导出",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate Limiter 状态和异常处理
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 挂载静态文件目录 (用于访问上传的 PDF 和其他文件)
import os
from fastapi.staticfiles import StaticFiles

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(entities_router)
app.include_router(ai_router)
app.include_router(rules_router)
app.include_router(tenants_router)
app.include_router(admin_router)
app.include_router(admin_export_router)
app.include_router(export_router)
app.include_router(upload_router)
app.include_router(departments_router)
app.include_router(dictionaries_router)
app.include_router(approvals_router)
app.include_router(remittances_router)
app.include_router(declarations_router)
app.include_router(logs_router)
app.include_router(sensitive_words_router)


@app.get("/", tags=["健康检查"])
async def root():
    return {
        "service": "ODI SaaS Platform",
        "version": "1.0.0",
        "status": "running",
        "llm_providers": llm_gateway.list_providers(),
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    return {"status": "healthy"}
