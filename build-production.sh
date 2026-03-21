#!/bin/bash
# 跨平台构建脚本 - 在 Mac ARM64 上构建 AMD64 镜像
# 用于在 Apple Silicon 上构建可在 Ubuntu x86_64 上运行的生产镜像

set -e

echo "🔨 构建后端镜像 (linux/amd64)..."
docker buildx build \
  --platform linux/amd64 \
  -f Dockerfile.backend \
  -t odi-saas-backend:latest \
  --load \
  ./backend

echo "🔨 构建前端镜像 (linux/amd64)..."
docker buildx build \
  --platform linux/amd64 \
  -f Dockerfile.frontend \
  -t odi-saas-frontend:latest \
  --load \
  .

echo "✅ 镜像构建完成！"
echo "   - odi-saas-backend:latest"
echo "   - odi-saas-frontend:latest"
echo ""
echo "📦 导出镜像："
echo "   docker save odi-saas-backend:latest | gzip > odi-saas-backend.tar.gz"
echo "   docker save odi-saas-frontend:latest | gzip > odi-saas-frontend.tar.gz"
