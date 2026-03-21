
# 智能 ODI 合规与出海服务管控 SaaS 平台 - AI 开发需求文档 (v1.0)

## 1. 项目概述 (Project Overview)

本项目旨在开发一款面向跨境出海企业的“智能 ODI (境外直接投资) 备案 SaaS 平台”。核心目标是通过**智能规则预审、多部委表单穿透复用 (Master Data)、以及 AI 驱动的尽调报告自动生成**，大幅降低代理机构和法务团队的人效成本。系统需支持多租户架构，并内置针对不同行业（如科技、电商）和特定国家（如香港、东南亚）的动态合规规则。

## 2. 推荐技术栈架构 (Tech Stack Recommendations)

考虑到系统包含较重的 AI 文本生成（Agent）逻辑和企业级表单流转，推荐如下架构选型，便于在现有的 Ubuntu 22.04 + GPU 算力环境下快速部署与迭代：

* **后端开发语言与框架：** Python + FastAPI（便于与大模型 API 或本地部署的开源模型无缝对接，适合高并发的异步处理）。
* **前端框架：** Vue 3 或 React（配合 Ant Design / Element Plus 等 B 端组件库搭建复杂工作台界面）。
* **数据库：** PostgreSQL（支持复杂的关联查询和 JSONB 字段，适合存储高度动态的表单数据）。
* **AI 与 Agent 层：** 预留接口对接外部大模型（如 GPT-4o, Claude 3.5），同时支持在本地显卡（如 Tesla T4 16G）上部署开源模型（如 Qwen 或 Llama 3）处理敏感财务数据提取和报告生成，确保数据合规不出境。

## 3. 核心角色与权限 (Roles & Permissions)

* **`CLIENT_USER` (客户)：** 提交基础信息，上传物料，查看进度看板，下载/签署最终文件。
* **`OPERATOR` (机构运营/合规专员)：** 审核资料，触发 AI 生成报告，人工精修，操作向政府系统的流转动作。
* **`ADMIN` (超级管理员)：** 维护国家/行业规则字典表，管理多租户与权限设置。

## 4. 核心业务流程与状态机 (Workflow & State Machine)

任何一个 ODI 项目（`Project`）的生命周期必须严格遵循以下状态流转：

1. `PRE_REVIEW` (意向测算与智能预审) -> 产生预审报告，红绿灯判断。
2. `DATA_COLLECTION` (立项与自动化材料准备) -> 客户传资料，AI 辅助生成报告及表单。
3. `NDRC_FILING_PENDING` (发改委备案准备) -> 导出/RPA 填报发改委系统。
4. `NDRC_APPROVED` (发改委获批) -> 需上传《备案通知书》。
5. `MOFCOM_FILING_PENDING` (商务部备案准备) -> 导出/RPA 填报商务部系统。
6. `MOFCOM_APPROVED` (商务部获批) -> 需上传《企业境外投资证书》。
7. `BANK_REG_PENDING` (银行外汇登记中)
8. `FUNDS_REMITTED` (资金已汇出 / 闭环)
9. `POST_INVESTMENT` (投后存量维系) -> 触发年度定时任务预警。

## 5. 核心数据模型设计参考 (Data Dictionary & ER)

开发需遵循 **“Master Data（主数据）全局复用”** 原则。以下为核心业务实体的字段定义：

### 5.1 `Entity_Domestic` (境内主体信息)

* `company_name` (String): 企业名称
* `uscc` (String): 统一社会信用代码
* `industry_code` (String): 境内行业分类代码
* `net_assets` (Decimal): 最近一年净资产（用于强制校验是否大于拟投资总额）
* `net_profit` (Decimal): 最近一年净利润

### 5.2 `Entity_Overseas` (境外投资标的信息)

* `overseas_name_cn` (String): 境外企业中文名
* `overseas_name_en` (String): 境外企业英文名
* `target_country` (String): 投资目的国/地区（联动风控规则引擎）
* `overseas_industry_code` (String): 境外主营业务代码
* `registered_capital` (Decimal): 注册资本/股本

### 5.3 `Project_Investment` (投资项目业务属性)

* `project_name` (String): 项目自动命名（规则：[境内主体]在[国家/地区]新设/并购[境外企业]项目）
* `investment_amount` (Decimal): 拟投资总额
* `currency` (Enum): 币种（USD/CNY等）
* `investment_path` (Enum): 投资架构（DIRECT/SPV_HK等）
* `funding_source` (JSON): 资金来源构成（自有资金、贷款比例）
* `purpose_description` (Text): 投资必要性说明（支持 AI 扩写）
* `status` (Enum): 当前所处审批阶段（映射状态机）

### 5.4 `Rules_Engine` (动态规则字典表 - 需高可配置)

* `rule_type` (Enum): 'COUNTRY' (国家), 'INDUSTRY' (行业)
* `target_value` (String): 如 'HK', 'Vietnam', 'E-commerce', 'AI'
* `risk_level` (Enum): 'HIGH', 'MEDIUM', 'LOW'
* `trigger_action` (JSON): 命中规则后的动作设定（如提示红筹架构搭建、提示外资持股上限 49%、提示技术出口管制等）。


## 6. AI 驱动层需求明细 (Cloud LLM API Matrix - 核心架构修正)

**业务决策：** 放弃本地 GPU 部署开源模型，全面采用云端大模型 API。目标模型为 DeepSeek、MiniMax、Kimi (Moonshot)。

**架构设计指导：**

* **大模型网关与工厂模式 (LLM Gateway & Factory Pattern)：** 后端需设计一个统一的 `LLM_Service` 接口。通过工厂模式封装不同厂商的 API 调用逻辑，实现底层模型的无缝热切换。
* **模型专长路由调度 (Model Routing)：**
* **文档长文本解析 (Kimi)：** 针对客户上传的长篇《审计报告》或复杂的境内财务报表，优先路由给 Kimi API（利用其 200k+ 超长上下文优势）进行 OCR 后的结构化关键指标（净资产、净利润）抽取。
* **核心逻辑判断与代码化生成 (DeepSeek)：** 用于执行智能预审的复杂合规逻辑判断，以及生成标准的 JSON 格式数据供业务流转。
* **《可研报告》润色与生成 (MiniMax / DeepSeek)：** 利用系统内部采集的 Master Data，组装复杂 Prompt，调用文本生成模型输出符合官方公文语气的《可行性研究报告》和《尽职调查报告》。


* **数据结构：** 建立 `LLM_Config` 表，允许系统管理员在后台配置各家 API Key、Base URL 及默认调用的模型版本。

---


## 7. 核心系统边界与确定的技术实现方案 (Core System Boundaries & Implementation)

基于业务侧的最终确认，系统需实现以下三个核心边界的架构设计：

### 7.1 外部企业征信数据源集成 (适配器模式)

**业务要求：** 支持企查查、天眼查、百度企业信用三家 API。
**架构设计指导：**

* **设计模式要求：** 后端需采用**策略模式 (Strategy Pattern)** 或 **适配器模式 (Adapter Pattern)** 封装企业信息查询服务 (`CorporateInfoService`)。
* **功能逻辑：** 系统需定义统一的内部数据结构（如统一映射为内部的 `DomesticCompanyDTO`）。配置层允许管理员动态切换默认数据源提供商；当主调用的 API（如企查查）限流或宕机时，系统需具备自动降级并切换至备用数据源（如天眼查）的机制。

### 7.2 政府政务系统数据对接 (标准化文件导出)

**业务要求：** 不做高风险的 RPA 直连，改为在系统内通过表格映射生成标准的 XML/Excel，供运营手动导入官方系统。
**架构设计指导：**

* **导出模块 (`Export_Engine`)：** 建立独立的模板映射引擎。业务流水线到达 `NDRC_FILING_PENDING` (发改委) 或 `MOFCOM_FILING_PENDING` (商务部) 状态时，系统提取主数据 (`Master Data`)。
* **模板配置化：** 提供可视化的字段映射配置表，将数据库字段映射为发改委要求的 XML 节点标签或商务部要求的 Excel 列。
* **生成与下载：** 提供“一键打包下载”接口，生成符合官方校验规则的 `.xml` 或 `.xlsx` 文件包，并打上时间戳。

### 7.3 多租户隔离与双轨制计费模型 (Tenant & Billing)

**业务要求：** 支持“按项目工单扣费”（Pay-as-you-go）和“按代理机构账号收取年费”（Annual Subscription）两种模式。
**架构设计指导与数据模型 (ER 补充)：**

* **`Tenant` (租户/代理机构表):**
* `tenant_id` (PK): 租户唯一标识（所有业务表均需包含此字段以实现数据逻辑隔离）。
* `agency_name` (String): 代理机构名称。
* `subscription_plan` (Enum): `FREE` (基础版), `ANNUAL` (年费会员).
* `subscription_expiry` (DateTime): 年费过期时间。
* `balance_credits` (Integer): 项目点数余额（用于按件扣费）。


* **`Billing_Log` (计费流水表):**
* `transaction_id` (PK).
* `tenant_id` (FK).
* `project_id` (FK): 关联的具体 ODI 项目。
* `billing_type` (Enum): `PROJECT_DEDUCTION` (工单扣点), `ANNUAL_RENEWAL` (年费充值), `CREDIT_TOPUP` (点数充值).
* `amount/credits_changed` (Decimal/Integer).


* **计费鉴权拦截器 (Billing Interceptor):**
* 在客户新建项目 (`Project_Create`) 或触发核心 AI 消耗环节时，系统优先校验 `Tenant` 的 `subscription_plan`。
* 如果是 `ANNUAL` 且在有效期内，直接放行（或记录 0 消耗）。
* 如果是 `FREE` 或非年费会员，检查 `balance_credits` 是否充足（如 >= 1 点）。充足则扣减 1 点并放行，否则阻断并抛出 `INSUFFICIENT_FUNDS` 错误，提示充值。


## 8. 部署与开发环境跨平台适配 (Cross-Platform DevOps Context)

**业务环境：** 开发机为 Apple Silicon (ARM64 架构)，生产目标服务器为 Ubuntu。由于取消了本地大模型部署，生产服务器不再强依赖 GPU 环境，转为标准的 CPU Web 服务架构。

**架构设计指导：**

* **跨平台构建 (Docker Buildx)：** AI 在生成 `Dockerfile` 和 `docker-compose.yml` 时，必须考虑架构差异。在 Mac ARM64 环境下编译生产镜像时，需强制指定目标平台。
* 提供基于 `docker buildx build --platform linux/amd64` 的构建脚本或 CI/CD (如 GitHub Actions/GitLab CI) 配置示例，确保在 Mac 上打出的镜像能在 Ubuntu (x86_64) 上正常运行。


* **开发环境配置：** 明确提供 `.env.development` 和 `.env.production` 环境变量模板。开发时直接使用 ARM64 兼容的基础镜像（如 `python:3.10-slim` 或 `node:18-alpine`），无需额外配置 NVIDIA 显卡驱动依赖。
* **服务精简：** 从服务编排中移除任何涉及 GPU 显存分配（如 `deploy.resources.reservations.devices`）的代码段。后端服务聚焦于高并发的 API 转发、数据库读写和文档 I/O 密集型任务。


