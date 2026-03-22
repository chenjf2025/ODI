# Changelog

All notable changes to this project will be documented in this file.

## [0.3.0] - 2026-03-23

### Added

- **AI 对话历史与反馈**
  - 对话历史侧边栏，支持查看历史会话
  - 消息反馈功能（点赞/点踩）
  - 用户消息支持复制和重新编辑
  - AI 回复支持重新生成
  - 跟进问题建议按钮

- **AI 报告中心**
  - 选择项目后自动加载已有报告
  - Markdown 内容渲染（标题、表格、列表、代码块、引用等）
  - Tab 切换展示（智能预审/可研报告/尽调报告）
  - PDF 导出功能（完整内容、无截断、正确边距）

- **项目文档审核**
  - 每个状态节点单独上传所需文件
  - 状态推进时自动触发 LLM 文件内容审核
  - 缺少必填文件时拦截推进并提示
  - 覆盖：材料准备、发改委备案、商务部备案、银行外汇登记、资金汇出、投后管理

- **项目状态中文显示**
  - AI助手查询项目状态时显示中文状态名（如"材料准备"而非"DATA_COLLECTION"）

### Fixed

- **nginx 上传代理**：新增 `/uploads/` 路径代理到后端 StaticFiles，解决文件上传后无法访问的问题
- **状态推进审核逻辑**：修复 document review 使用目标状态而非当前状态的 bug
- **utc_now 时区问题**：修复数据库时间字段时区不兼容导致的推进失败
- **PDF 导出**：修复导出空白、内容截断、边距缺失、字体异常等问题

## [0.2.0] - 2026-03-22

### Added

- **AI Workspace（AI 工作台）**
  - 全新统一对话界面（类 Gemini 风格），支持 intent 路由：闲聊、ODI 合规咨询、预审报告、常识问答
  - 以独立菜单项置于工作台上方，作为平台首个主功能入口
  - 支持流式回复展示

- **Dify 知识库集成**
  - 对接 Dify SaaS 平台，实现 KNOWLEDGE_QA intent 的 RAG 检索问答
  - 支持 DeepSeek / Ollama 多模型后端
  - Dify 应用 API Key、Base URL、App ID、Dataset ID 全链路可配置
  - 知识库文档检索结果自动附加到 LLM 上下文中

- **对话历史保存**
  - 用户每次 AI 对话内容实时写入数据库
  - 支持历史记录查询与展示

- **完整中英文 README**
  - 项目介绍、技术架构、API 文档、快速启动指南
  - 新增 LLM 提供商扩展文档

### Fixed

- **AI Workspace 输入框缺失**
  - 问题：AI Workspace 对话框没有输入框，无法发送消息
  - 解决：将 AI 智能助手独立成独立页面，重新设计输入组件布局

- **Dify API 400 错误**
  - 问题：Dify `/v1/datasets/{id}/retrieve` 返回 401，后改用 chat API
  - 解决：切换到 `POST /v1/chat-messages` 接口，blocking 模式获取回答

- **Dify inputs 格式错误**
  - 问题：Dify chat API 返回 422，提示 inputs 字段格式不对
  - 解决：`inputs` 从 `{"message": query}` 改为 `{}`（Dify 知识问答只需 query 参数）

- **Dify 响应字段名错误**
  - 问题：Dify API 实际返回 `{"answer": "..."}`，但代码用 `response` 字段提取
  - 解决：`dify_result.get("response", ...)` → `dify_result.get("answer", ...)`

- **Docker 宿主机访问问题**
  - 问题：后端容器内访问本地 Dify（localhost:8080）无法连接
  - 解决：Mac/Windows 环境下使用 `host.docker.internal` 作为 DIFY_BASE_URL

### Changed

- `docker-compose.yml`：新增 `DIFY_*` 环境变量配置段
- `.env.example`：补充 Dify 相关环境变量说明
- `dify_service.py`：重构为 class-based service，统一 chat 与 retrieve 方法

---

## [0.1.0] - 2026-03-21

### Added

- ODI SaaS 平台核心框架
  - 用户认证（JWT + Refresh Token + RBAC）
  - 租户管理系统
  - 项目全生命周期管理（9阶段状态机）
  - 境内/境外主体管理
  - AI 智能预审（DeepSeek / Kimi / MiniMax 自动路由）
  - AI 报告生成（可行性研究、尽职调查）
  - 多部委表单导出（发改委 XML、商务部 Excel）
  - 点数计费系统
  - 合规规则引擎
  - LLM 配置管理后台
