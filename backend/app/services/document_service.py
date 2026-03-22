from typing import Dict, List
from app.models.project import ProjectStatus
from app.services.ai_service import ai_service
from app.models.project_document import ProjectDocument
from app.services.llm.router import TaskType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID


STEP_DOCUMENT_REQUIREMENTS: Dict[str, List[Dict]] = {
    "DATA_COLLECTION": [
        {
            "type": "business_license",
            "name": "境内企业营业执照",
            "required": True,
            "description": "境内投资主体最新有效的营业执照副本（加盖公章）",
        },
        {
            "type": "company_charter",
            "name": "公司章程",
            "required": True,
            "description": "境内投资主体最新公司章程",
        },
        {
            "type": "feasibility_report",
            "name": "可行性研究报告",
            "required": True,
            "description": "境外投资项目可行性研究报告（包括投资背景、目的、市场分析、财务预测等）",
        },
        {
            "type": "fund_source_proof",
            "name": "资金来源证明",
            "required": True,
            "description": "银行资信证明、存款证明或贷款意向书，证明投资资金来源合法",
        },
        {
            "type": "audit_report",
            "name": "近一年审计报告",
            "required": True,
            "description": "境内投资主体近一年经审计的财务报表",
        },
    ],
    "NDRC_FILING_PENDING": [
        {
            "type": "project_application",
            "name": "项目申请报告",
            "required": True,
            "description": "《境外投资项目管理 проб类项目申请报告》，包括投资主体情况、境外企业情况、投资背景、必要性分析、投资方案、资金方案、风险分析等",
        },
        {
            "type": "ndrc_filing_form",
            "name": "境外投资项目备案/核准申请表",
            "required": True,
            "description": "通过全国境外投资项目在线管理服务平台填报并打印",
        },
        {
            "type": "feasibility_report_ndrc",
            "name": "可行性研究报告（发改委用）",
            "required": True,
            "description": "须由有资质的工程咨询机构出具",
        },
        {
            "type": "domestic_entity_info",
            "name": "境内投资主体材料",
            "required": True,
            "description": "营业执照复印件、相关资质证明（如有）",
        },
        {
            "type": "overseas_entity_info",
            "name": "境外目标企业/项目材料",
            "required": True,
            "description": "境外企业注册文件、项目批文（如有）",
        },
    ],
    "NDRC_APPROVED": [
        {
            "type": "ndrc_filing_notice",
            "name": "发改委备案通知书/核准批复",
            "required": True,
            "description": "国家发展改革委出具的《境外投资项目备案证明》或《核准批复》",
        },
        {
            "type": "ndrc_receipt",
            "name": "发改委受理凭证",
            "required": False,
            "description": "在线申报系统生成的受理单据",
        },
    ],
    "MOFCOM_FILING_PENDING": [
        {
            "type": "mofcom_application",
            "name": "境外投资申请表",
            "required": True,
            "description": "《境外投资申请表》，通过境外投资管理系统在线填报并打印",
        },
        {
            "type": "business_license_mofcom",
            "name": "营业执照",
            "required": True,
            "description": "境内投资主体营业执照复印件（加盖公章）",
        },
        {
            "type": "investment_contract",
            "name": "投资协议或合同",
            "required": True,
            "description": "与境外合作方签订的投资协议、合资合同或并购协议（如已签署）",
        },
        {
            "type": "ndrc_filing_notice_mofcom",
            "name": "发改委备案通知书",
            "required": True,
            "description": "已取得的发改委备案通知书或核准批复复印件",
        },
        {
            "type": "overseas_entity_registration",
            "name": "境外企业注册文件",
            "required": False,
            "description": "境外企业的注册登记文件、公司章程等（如已设立）",
        },
    ],
    "MOFCOM_APPROVED": [
        {
            "type": "odi_certificate",
            "name": "企业境外投资证书",
            "required": True,
            "description": "商务部颁发的《企业境外投资证书》（正式版）",
        },
        {
            "type": "mofcom_filing_receipt",
            "name": "商务部备案回执",
            "required": False,
            "description": "在线申报系统的申报回执",
        },
    ],
    "BANK_REG_PENDING": [
        {
            "type": "ndrc_filing_notice_bank",
            "name": "发改委备案通知书/核准文件",
            "required": True,
            "description": "发改委出具的《备案通知书》或《核准文件》原件及复印件",
        },
        {
            "type": "odi_certificate_bank",
            "name": "企业境外投资证书",
            "required": True,
            "description": "商务部颁发的《企业境外投资证书》原件及复印件",
        },
        {
            "type": "business_license_bank",
            "name": "营业执照",
            "required": True,
            "description": "境内投资主体营业执照原件及复印件（加盖公章）",
        },
        {
            "type": "fund_source_bank",
            "name": "资金来源证明（银行用）",
            "required": True,
            "description": "银行资信证明、审计报告、资产负债表等，证明资金来源真实合法",
        },
        {
            "type": "bank_account_opening",
            "name": "境内外账户信息",
            "required": True,
            "description": "境内外银行账户开户证明",
        },
        {
            "type": "foreign_exchange_application",
            "name": "外汇业务申请表",
            "required": True,
            "description": "根据银行要求填写的境外直接投资外汇登记申请表",
        },
    ],
    "FUNDS_REMITTED": [
        {
            "type": "bank_remittance_receipt",
            "name": "银行汇款凭证",
            "required": True,
            "description": "银行出具的资金汇出凭证/水单",
        },
        {
            "type": "exchange_rate_proof",
            "name": "汇率证明",
            "required": False,
            "description": "如有大额汇率兑换，需提供汇率证明",
        },
    ],
    "POST_INVESTMENT": [
        {
            "type": "investment_completion_report",
            "name": "投资完成报告",
            "required": True,
            "description": "境外投资实际完成情况报告（包括实际投资金额、资金汇出时间等）",
        },
        {
            "type": "overseas_company_status",
            "name": "境外企业存续证明",
            "required": True,
            "description": "境外企业存续证明文件（注册文件、良好存续证明等）",
        },
        {
            "type": "financial_report_overseas",
            "name": "境外企业财务报告",
            "required": False,
            "description": "境外企业近一年财务报表（如有）",
        },
    ],
}


def get_step_requirements(step_status: str) -> List[Dict]:
    return STEP_DOCUMENT_REQUIREMENTS.get(step_status, [])


def get_all_required_documents_for_step(step_status: str) -> List[str]:
    reqs = get_step_requirements(step_status)
    return [r["type"] for r in reqs if r.get("required")]


async def review_documents_for_step(
    db: AsyncSession,
    project_id: UUID,
    step_status: str,
) -> Dict:
    requirements = get_step_requirements(step_status)
    if not requirements:
        return {"passed": True, "message": "该环节无特定文件要求"}

    result = await db.execute(
        select(ProjectDocument).where(
            ProjectDocument.project_id == project_id,
            ProjectDocument.step_status == step_status,
        )
    )
    uploaded_docs = {doc.document_type: doc for doc in result.scalars().all()}

    required_types = {r["type"]: r for r in requirements if r.get("required")}
    missing = [
        required_types[t]["name"] for t in required_types if t not in uploaded_docs
    ]
    if missing:
        return {
            "passed": False,
            "message": f"缺少以下必填文件：{'、'.join(missing)}",
            "missing": missing,
        }

    prompt_parts = [
        f"请审查以下境外投资项目中【{_status_name(step_status)}】环节所需提交的文件。",
        f"项目信息：待审查项目 ID {project_id}",
        "\n各文件内容如下：\n",
    ]
    for doc_type, doc in uploaded_docs.items():
        req_info = required_types.get(doc_type, {})
        prompt_parts.append(f"【{req_info.get('name', doc_type)}】({doc_type}):")
        prompt_parts.append(f"  文件名：{doc.document_name}")
        prompt_parts.append(f"  内容：{doc.file_url}")
        prompt_parts.append("")

    prompt_parts.append(
        "\n请从以下维度审核：\n"
        "1. 文件内容是否与所需文件类型匹配\n"
        "2. 文件是否完整、清晰可读\n"
        "3. 文件是否存在明显错误或虚假内容\n"
        "4. 给出通过/不通过结论及原因"
    )

    prompt = "\n".join(prompt_parts)
    try:
        llm_resp = await ai_service.router.route_and_call(
            task_type=TaskType.LOGIC_JUDGE,
            messages=[
                {
                    "role": "system",
                    "content": "你是一位专业的境外投资合规顾问，擅长审核 ODI 项目各环节所需提交的文件资料。请严格审查文件的相关性、完整性和真实性。",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2048,
        )
        review_result = llm_resp.content
    except Exception as e:
        review_result = f"AI 审核暂不可用：{type(e).__name__}: {str(e)}"

    for doc in uploaded_docs.values():
        doc.review_result = review_result
        doc.review_status = "reviewed"
    await db.flush()

    return {
        "passed": True,
        "message": "文件审核完成",
        "review_result": review_result,
        "uploaded": list(uploaded_docs.keys()),
    }


_STATUS_NAME = {
    "DATA_COLLECTION": "材料准备",
    "NDRC_FILING_PENDING": "发改委备案",
    "NDRC_APPROVED": "发改委获批",
    "MOFCOM_FILING_PENDING": "商务部备案",
    "MOFCOM_APPROVED": "商务部获批",
    "BANK_REG_PENDING": "银行外汇登记",
    "FUNDS_REMITTED": "资金汇出",
    "POST_INVESTMENT": "投后管理",
}


def _status_name(s: str) -> str:
    return _STATUS_NAME.get(s, s)
