#!/bin/bash

# VintageWisdom 数据恢复脚本
# 使用方法: ./scripts/restore.sh <backup_file>

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ $# -eq 0 ]; then
    echo -e "${RED}错误: 请指定备份文件${NC}"
    echo "使用方法: $0 <backup_file>"
    echo "示例: $0 ~/backups/vintagewisdom/vintagewisdom_full_20240101_120000.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMP_DIR="/tmp/vw_restore_$$"

if [ ! -f "${BACKUP_FILE}" ]; then
    echo -e "${RED}错误: 备份文件不存在: ${BACKUP_FILE}${NC}"
    exit 1
fi

echo "========================================="
echo "  VintageWisdom 数据恢复"
echo "========================================="
echo ""
echo -e "${YELLOW}警告: 此操作将覆盖现有数据！${NC}"
read -p "确认继续? [y/N]: " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "恢复已取消"
    exit 0
fi

cd "${PROJECT_DIR}"

# 1. 停止服务
echo "1. 停止服务..."
docker compose -f docker-compose.prod.yml stop backend
echo -e "${GREEN}✓ 服务已停止${NC}"

# 2. 解压备份
echo "2. 解压备份文件..."
mkdir -p "${TEMP_DIR}"
tar -xzf "${BACKUP_FILE}" -C "${TEMP_DIR}"
echo -e "${GREEN}✓ 备份文件已解压${NC}"

# 3. 恢复数据库
echo "3. 恢复数据库..."
if [ -f "${TEMP_DIR}"/backup_*.db ]; then
    DB_FILE=$(ls "${TEMP_DIR}"/backup_*.db | head -1)
    docker cp "${DB_FILE}" vw_backend:/app/data/vintagewisdom.db
    echo -e "${GREEN}✓ 数据库已恢复${NC}"
else
    echo -e "${YELLOW}⚠ 未找到数据库备份文件${NC}"
fi

# 4. 恢复配置文件
echo "4. 恢复配置文件..."
if [ -f "${TEMP_DIR}"/config_*.tar.gz ]; then
    CONFIG_FILE=$(ls "${TEMP_DIR}"/config_*.tar.gz | head -1)
    tar -xzf "${CONFIG_FILE}" -C "${PROJECT_DIR}"
    echo -e "${GREEN}✓ 配置文件已恢复${NC}"
else
    echo -e "${YELLOW}⚠ 未找到配置文件备份${NC}"
fi

# 5. 恢复用户数据
echo "5. 恢复用户数据..."
if [ -f "${TEMP_DIR}"/data_*.tar.gz ]; then
    DATA_FILE=$(ls "${TEMP_DIR}"/data_*.tar.gz | head -1)
    tar -xzf "${DATA_FILE}" -C "${PROJECT_DIR}"
    echo -e "${GREEN}✓ 用户数据已恢复${NC}"
else
    echo -e "${YELLOW}⚠ 未找到用户数据备份${NC}"
fi

# 6. 清理临时文件
echo "6. 清理临时文件..."
rm -rf "${TEMP_DIR}"
echo -e "${GREEN}✓ 临时文件已清理${NC}"

# 7. 重启服务
echo "7. 重启服务..."
docker compose -f docker-compose.prod.yml start backend
sleep 5

# 8. 健康检查
echo "8. 执行健康检查..."
HEALTH=$(docker compose -f docker-compose.prod.yml exec -T backend curl -f http://localhost:8000/health 2>/dev/null || echo "failed")

echo ""
echo "========================================="
echo "  恢复完成"
echo "========================================="
echo ""
echo "服务状态: ${HEALTH}"
echo ""

if [ "${HEALTH}" != "failed" ]; then
    echo -e "${GREEN}✓ 数据恢复成功，服务运行正常${NC}"
else
    echo -e "${RED}✗ 服务健康检查失败，请检查日志${NC}"
    echo "查看日志: docker compose -f docker-compose.prod.yml logs backend"
fi
