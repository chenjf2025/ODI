# ODI 架构与部署指南

> 本文档详细介绍 ODI SaaS 平台的技术架构、LLM/Embedding/Rerank 模型配置，以及 Dify 知识库的完整部署流程。

---

## 目录

- [1. 系统架构总览](#1-系统架构总览)
- [2. 组件依赖关系](#2-组件依赖关系)
- [3. Dify 部署指南](#3-dify-部署指南)
- [4. LLM 模型配置](#4-llm-模型配置)
- [5. Embedding 模型配置](#5-embedding-模型配置)
- [6. Rerank 模型配置](#6-rerank-模型配置)
- [7. Dify 知识库配置](#7-dify-知识库配置)
- [8. ODI 环境变量](#8-odi-环境变量)
- [9. 一键启动脚本](#9-一键启动脚本)
- [10. 生产环境部署](#10-生产环境部署)
- [11. 常见问题与排查](#11-常见问题与排查)

---

## 1. 系统架构总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户浏览器                                       │
│                         http://localhost (前端)                               │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │ HTTP / WebSocket
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Nginx 反向代理                                       │
│                     (端口 80/443，SSL 终止)                                   │
└───────────────────────────────┬─────────────────────────────────────────────┘
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
┌───────────────┐                             ┌───────────────┐
│  前端 Vue 3   │                             │  后端 FastAPI │
│  (端口 80)    │                             │  (端口 8000)  │
└───────────────┘                             └───────┬───────┘
                                                      │
                              ┌───────────────────────┼───────────────────────┐
                              │                       │                       │
                              ▼                       ▼                       ▼
                    ┌──────────────┐         ┌──────────────┐       ┌──────────────┐
                    │  PostgreSQL  │         │  Dify 服务    │       │  LLM 提供商   │
                    │   (5432)     │         │  (8080)       │       │  (云端/本地)  │
                    └──────────────┘         └───────┬──────┘       └───────┬──────┘
                                                     │                       │
                                                     ▼                       │
                                          ┌──────────────────┐              │
                                          │ Dify 内置 RAG    │              │
                                          │  + Embedding     │              │
                                          │  + Rerank        │              │
                                          │  (可选外部)      │              │
                                          └──────────────────┘              │
                                                     │                       │
                                                     ▼                       ▼
                                          ┌──────────────────┐    ┌──────────────────┐
                                          │ Ollama 本地模型   │    │  DeepSeek / Kimi  │
                                          │ - LLM (qwen3)    │    │  (云端 API)       │
                                          │ - Embedding      │    │                   │
                                          │   (qwen3-embed)  │    │                   │
                                          └──────────────────┘    └──────────────────┘
```

### 核心组件

| 组件 | 用途 | 端口 | 必需 |
|------|------|------|------|
| ODI Frontend | Vue 3 + Ant Design Vue 前端 | 80 | ✅ |
| ODI Backend | FastAPI 后端 API | 8000 | ✅ |
| PostgreSQL 16 | 主数据库 | 5432 | ✅ |
| Nginx | 反向代理 + 静态文件服务 | 80/443 | ✅ |
| Dify | 知识库 RAG 引擎 | 8080 | ⚡ 推荐 |
| Ollama | 本地 LLM + Embedding | 11434 | 可选 |
| DeepSeek / Kimi | 云端 LLM | - | 可选 |

---

## 2. 组件依赖关系

```
ODI Backend
    ├── 依赖 PostgreSQL（必须）
    ├── 依赖 Dify API（知识库问答必须）
    │       └── 依赖 Ollama（Embedding 必须）
    │               └── 依赖 qwen3-embedding 模型
    └── 依赖 LLM 提供商
            ├── DeepSeek（云端，默认）
            ├── Kimi（云端，备用）
            ├── MiniMax（云端，备用）
            └── Ollama（本地，私有大模型）

Dify 服务
    ├── 依赖 Ollama Embedding（文档向量化）
    ├── 依赖 Rerank 模型（可选，检索结果重排序）
    └── 依赖 LLM（生成回答）
            ├── Ollama 本地 qwen3
            └── DeepSeek 云端
```

**启动顺序**：PostgreSQL → Ollama → Dify → ODI Backend → Nginx → Frontend

---

## 3. Dify 部署指南

### 3.1 方式一：Docker 快速部署（推荐）

```bash
# 克隆 Dify
git clone https://github.com/langgenius/dify.git /tmp/dify-deploy
cd /tmp/dify-deploy/docker

# 复制环境变量模板
cp .env.example .env

# 修改 .env（关键配置）
vim .env
```

**.env 关键配置**：

```env
# ===== Dify 数据库 =====
DB_USERNAME=odify
DB_PASSWORD=odify_pass
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=dify

# ===== Dify Service =====
SECRET_KEY=your-32-char-secret-key-here
CONSOLE_WEB_URL=http://localhost:8080
CONSOLE_API_URL=http://localhost:8080
APP_WEB_URL=http://localhost:8080

# ===== Ollama 集成（本地模型）=====
# Mac/Windows: 使用 host.docker.internal
# Linux: 使用宿主机的实际 IP
OLLAMA_BASE_URL=http://host.docker.internal:11434

# ===== 模型供应商 =====
MODEL_PROVIDER_OLLAMA_ENABLED=true
```

**启动 Dify**：

```bash
docker-compose up -d

# 验证 11 个容器是否全部运行
docker ps --format "table {{.Names}}\t{{.Status}}"
```

**预期输出**：
```
dify-api-1              Up
dify-web-1              Up
dify-worker-1           Up
dify-db-1               Up
dify/redis-1            Up
dify/nginx-1             Up
dify/qdrant-1           Up
dify/middleware-1       Up
dify/weaviate-1         Up
dify/valves-1           Up
dify/embedding-1        Up
```

访问 http://localhost:8080，创建管理员账户。

### 3.2 方式二：仅外部使用 Dify（不自建 Dify）

如果团队已有 Dify Cloud 或其他 Dify 实例，只需配置 API Key 即可：

```env
DIFY_BASE_URL=https://your-dify-instance.com
DIFY_API_KEY=app-xxxxx
DIFY_APP_ID=cb0819a8-xxxxx
DIFY_DATASET_ID=cf20d873-xxxxx
```

---

## 4. LLM 模型配置

ODI 支持多个 LLM 提供商，按优先级自动路由。

### 4.1 云端 LLM（推荐先跑通流程）

**DeepSeek**（默认，优先级最高）：

```env
DEEPSEEK_API_KEY=sk-xxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

**Kimi**（Moonshot，备用）：

```env
KIMI_API_KEY=sk-xxxxx
KIMI_BASE_URL=https://api.moonshot.cn/v1
```

**MiniMax**（备用）：

```env
MINIMAX_API_KEY=xxxxx
MINIMAX_BASE_URL=https://api.minimax.chat/v1
```

### 4.2 本地 LLM（Ollama）

适合数据隐私要求高、想节省 API 费用的场景。

**安装 Ollama**：

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: 从 https://ollama.com/download 下载安装
```

**拉取模型**：

```bash
# 通用对话模型（推荐 qwen3 系列）
ollama pull qwen3:8b

# 更大参数模型（需要更多显存）
ollama pull qwen3:32b

# 中文优化模型
ollama pull deepseek-r1:14b
```

**配置 Ollama 为 Dify 的模型供应商**：

在 Dify 控制台 → 设置 → 模型供应商 → Ollama：
- Base URL：`http://host.docker.internal:11434`（Mac/Windows）或 `http://your-host-ip:11434`（Linux）
- 点击 "Check API Connection" 验证

### 4.3 本地 LLM 作为 ODI 后端直接调用

ODI 后端可以直接调用本地 Ollama（不经过 Dify）：

```env
# 在 ODI .env 中添加
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_API_KEY=ollama  # Ollama 不需要真实 key，随便填
OLLAMA_MODEL=qwen3:8b
```

然后在 ODI 管理后台添加 Ollama 为 LLM 提供商。

---

## 5. Embedding 模型配置

Embedding 模型用于将文本向量化，是知识库检索的基础。

### 5.1 Dify 内置 Embedding（默认）

Dify 自带的 embedding 模型，开箱即用，适合快速启动。

### 5.2 Ollama 本地 Embedding（推荐国内用户）

使用 qwen3-embedding 模型，完全本地运行，无需 API 费用。

**拉取 Embedding 模型**：

```bash
ollama pull qwen3-embedding:4b
```

**配置 Dify 使用 Ollama Embedding**：

1. Dify 控制台 → 设置 → 模型供应商 → Ollama
2. 添加 Embedding 模型：`qwen3-embedding:4b`
3. 设置为知识库的默认 Embedding 模型

**验证 Embedding 是否正常工作**：

```bash
curl http://localhost:11434/api/tags
```

确认输出中包含 `qwen3-embedding`。

### 5.3 OpenAI 兼容 Embedding

如果使用 OpenAI 或兼容 API 的 Embedding 服务：

```env
OPENAI_EMBEDDING_API_KEY=sk-xxxxx
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

---

## 6. Rerank 模型配置

Rerank（重排序）模型用于在 Embedding 检索之后对结果进行二次排序，显著提升检索质量。

### 6.1 何时需要 Rerank

| 场景 | 不需要 Rerank | 需要 Rerank |
|------|--------------|-------------|
| 知识库文档 < 1000 篇 | ✅ | 可选 |
| 知识库文档 > 1000 篇 | | ✅ 强烈推荐 |
| 查询与文档存在语义差异 | | ✅ |
| 精确匹配要求高 | | ✅ |

### 6.2 Dify 支持的 Rerank 模型

| Rerank 提供商 | 模型 | 说明 |
|-------------|------|------|
| Cohere | rerank-multilingual | 支持多语言，效果好 |
| OpenAI | gpt rerank | 需 API 费用 |
| Ollama | 第三方 rerank 模型 | 本地运行 |

### 6.3 配置 Cohere Rerank

1. 获取 [Cohere API Key](https://cohere.com/)
2. Dify 控制台 → 设置 → 模型供应商 → Cohere
3. 添加 Rerank 模型：`rerank-multilingual-v3.0`
4. 在知识库设置中启用 Rerank

```env
COHERE_API_KEY=xxxxx
```

### 6.4 本地 Rerank（实验性）

如果想完全本地运行，可以使用支持 Rerank 的开源模型（如 bge-reranker）：

```bash
# 安装 bge-reranker（通过 Dify 插件或单独部署）
# 参考：https://github.com/FlagOpen/FlagEmbedding
```

---

## 7. Dify 知识库配置

### 7.1 创建知识库

1. 访问 http://localhost:8080/datasets
2. 点击 "创建知识库"
3. 选择 Embedding 模型（推荐 qwen3-embedding:4b）
4. 可选：启用 Rerank 模型

### 7.2 上传文档

支持格式：PDF、TXT、Markdown、HTML、Word、CSV

**推荐配置**：

| 配置项 | 推荐值 | 说明 |
|--------|--------|------|
| 解析方法 | High Quality | 付费但准确率高 |
| 分块大小 | 500 tokens | 太长降低检索精度，太短丢失上下文 |
| 分块重叠 | 50 tokens | 保持上下文连贯 |
| Embedding 模型 | qwen3-embedding:4b | 本地，无需费用 |

### 7.3 创建 Dify 应用并关联知识库

1. Dify 控制台 → 创建应用 → 选择 "Chatflow" 或 "Agent"
2. 在应用内添加 "Knowledge Retrieval" 节点
3. 关联已创建的知识库
4. 设置引用重排序（启用 Rerank）

### 7.4 获取 Dify API 凭证

应用创建完成后：
1. 打开应用 → 设置 → API Key
2. 点击 "创建 API Key"
3. 记录 App ID 和 API Key

**获取 Dataset ID**：
- 知识库列表 → 点击知识库 → 地址栏或设置页中找到 Dataset ID

### 7.5 配置 ODI 环境变量

将以下变量填入 ODI 的 `.env` 文件：

```env
# Dify API 凭证（必需）
DIFY_API_KEY=app-xxxxxxxxxxxx
DIFY_BASE_URL=http://host.docker.internal:8080
DIFY_APP_ID=cb0819a8-a096-4d0d-b947-c5699661a650
DIFY_DATASET_ID=cf20d873-9273-42e1-b57e-b3f38e3012bd
```

**注意**：
- Mac/Windows：`DIFY_BASE_URL=http://host.docker.internal:8080`
- Linux：`DIFY_BASE_URL=http://<宿主机器IP>:8080`

---

## 8. ODI 环境变量

完整环境变量模板见 `.env.example`，以下是各配置项说明：

```env
# ===== 数据库 =====
DATABASE_URL=postgresql+asyncpg://odi_user:odi_pass@db:5432/odi_saas
DATABASE_SYNC_URL=postgresql://odi_user:odi_pass@db:5432/odi_saas

# ===== JWT（生产必填） =====
JWT_SECRET_KEY=your-32-char-random-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# ===== CORS（生产禁止 localhost） =====
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# ===== LLM 提供商（至少配置一个）=====
# DeepSeek（默认）
DEEPSEEK_API_KEY=sk-xxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Kimi（备用）
KIMI_API_KEY=sk-xxxxx
KIMI_BASE_URL=https://api.moonshot.cn/v1

# MiniMax（备用）
MINIMAX_API_KEY=xxxxx
MINIMAX_BASE_URL=https://api.minimax.chat/v1

# ===== Dify 知识库（知识问答必需）=====
DIFY_API_KEY=app-xxxxxxxxxxxx
DIFY_BASE_URL=http://host.docker.internal:8080
DIFY_APP_ID=cb0819a8-xxxxx
DIFY_DATASET_ID=cf20d873-xxxxx

# ===== 企业征信（可选）=====
QICHACHA_API_KEY=xxxxx
TIANYANCHA_API_KEY=xxxxx
BAIDU_CREDIT_API_KEY=xxxxx
```

---

## 9. 一键启动脚本

```bash
#!/bin/bash
# deploy_odi.sh - ODI 完整部署脚本

set -e

echo "=== 1. 启动 Dify ==="
cd /tmp/dify-deploy/docker
docker-compose up -d
echo "等待 Dify 启动..."
sleep 30

echo "=== 2. 启动 ODI Backend ==="
cd /path/to/ODI
docker-compose up -d backend
sleep 5

echo "=== 3. 启动前端 ==="
docker-compose up -d frontend

echo "=== 验证服务 ==="
echo "ODI 前端: http://localhost"
echo "ODI 后端: http://localhost:8000/docs"
echo "Dify:     http://localhost:8080"

docker ps --format "table {{.Names}}\t{{.Status}}"
```

---

## 10. 生产环境部署

### 10.1 服务器要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 4 核 | 8 核 |
| 内存 | 16 GB | 32 GB |
| 磁盘 | 50 GB SSD | 200 GB SSD |
| GPU | 可选 | NVIDIA 16GB+ 显存（跑本地模型） |

### 10.2 域名与 SSL

```nginx
# /etc/nginx/sites-available/odi
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 10.3 环境变量（生产）

```env
APP_ENV=production
APP_DEBUG=false
CORS_ORIGINS=https://your-domain.com

# 使用强随机密钥
JWT_SECRET_KEY=<openssl rand -base64 32>

# 数据库连接（生产建议云数据库）
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/odi_saas
```

---

## 11. 常见问题与排查

### Q1: Dify 容器启动失败

**症状**：`docker-compose up -d` 后容器Exited

```bash
# 查看日志
docker-compose logs api
docker-compose logs worker

# 常见原因：端口冲突
netstat -tlnp | grep 5432
```

**解决**：确保 5432、6379、8080、9200 端口未被占用。

---

### Q2: Dify API 返回 401/403

**症状**：调用 Dify 接口返回未授权错误

**排查**：
1. 检查 API Key 是否正确
2. 检查 App ID 是否与创建的应用匹配
3. 确认应用已发布（未发布的应用无法通过 API 调用）

**解决**：
```bash
# 测试 API Key 是否有效
curl -X POST 'http://localhost:8080/v1/chat-messages' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{"inputs": {}, "query": "test", "response_mode": "blocking", "user": "test"}'
```

---

### Q3: Dify 422 Unprocessable Entity

**症状**：`inputs` 字段格式错误

**原因**：Dify chat API 的 `inputs` 应为空对象 `{}`，而非 `{"message": query}`

**解决**（已修复于 ODI 后端）：
```python
# 错误
payload = {"inputs": {"message": query}, ...}

# 正确
payload = {"inputs": {}, "query": query, ...}
```

---

### Q4: Embedding 模型无法连接

**症状**：上传文档时报 Embedding 连接错误

**排查**：
1. 确认 Ollama 已启动：`curl http://localhost:11434/api/tags`
2. 确认 qwen3-embedding 模型已拉取
3. 确认 Dify 中 Ollama 配置的 URL 正确

```bash
# Mac/Windows Dify 访问宿主机 Ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434

# Linux Dify 访问宿主机
OLLAMA_BASE_URL=http://<实际IP>:11434
```

---

### Q5: "Dify 未返回有效响应"

**症状**：ODI AI 对话显示此错误

**原因**：代码提取字段名与 Dify API 返回不一致

**解决**（已修复于 ODI 后端）：
```python
# 错误
response_text = dify_result.get("response", "Dify 未返回有效响应")

# 正确（Dify 返回 answer 字段）
response_text = dify_result.get("answer", "Dify 未返回有效响应")
```

---

### Q6: 知识库检索结果为空

**排查步骤**：
1. 确认文档已上传且状态为"已完成"
2. 确认 Dataset ID 正确
3. 测试直接调用 Dify：

```bash
curl -X POST 'http://localhost:8080/v1/chat-messages' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -d '{"inputs": {}, "query": "你的查询关键词", "response_mode": "blocking", "user": "test"}'
```

如果返回结果中 `retriever_resources` 为空，说明知识库检索失败。

---

### Q7: 容器内无法访问 Dify

**症状**：ODI 后端在 Docker 容器内运行，无法连接 `localhost:8080`

**原因**：Docker 容器内的 `localhost` 指向容器自己，而非宿主机

**解决**：

| 系统 | DIFY_BASE_URL |
|------|---------------|
| Mac | `http://host.docker.internal:8080` |
| Windows | `http://host.docker.internal:8080` |
| Linux | `http://<宿主IP>:8080`（不能用 host.docker.internal）|

Linux 查看宿主机 IP：
```bash
ip route get 1 | awk '{print $(NF-2); exit}'
```

---

### Q8: 节省 API 费用——本地 vs 云端

| 方案 | Embedding | LLM 对话 | Rerank | 费用 |
|------|-----------|---------|--------|------|
| 全云端 | Dify 内置 | DeepSeek | Cohere | 按量付费 |
| 半本地 | Ollama qwen3-embedding | DeepSeek | Cohere | Embedding 免费 |
| 全本地 | Ollama qwen3-embedding | Ollama qwen3 | Ollama | **全部免费** |

**推荐起步**：先用云端 LLM + 本地 Embedding（qwen3-embedding），确认流程跑通后再逐步迁移到全本地。
