#!/bin/bash

# VintageWisdom 数据备份脚本
# 使用方法: ./scripts/backup.sh

set -e

# 配置
BACKUP_DIR="${HOME}/backups/vintagewisdom"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=30

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================="
echo "  VintageWisdom 数据备份"
echo "========================================="
echo ""

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

cd "${PROJECT_DIR}"

# 1. 备份 SQLite 数据库
echo "1. 备份数据库..."
if docker compose -f docker-compose.prod.yml ps | grep -q "vw_backend.*Up"; then
    docker compose -f docker-compose.prod.yml exec -T backend \
        sqlite3 /app/data/vintagewisdom.db ".backup /app/data/backup_${DATE}.db"
    
    docker cp vw_backend:/app/data/backup_${DATE}.db "${BACKUP_DIR}/"
    docker compose -f docker-compose.prod.yml exec -T backend \
        rm /app/data/backup_${DATE}.db
    
    echo -e "${GREEN}✓ 数据库备份完成${NC}"
else
    echo -e "${YELLOW}⚠ 后端服务未运行，跳过数据库备份${NC}"
fi

# 2. 备份配置文件
echo "2. 备份配置文件..."
tar -czf "${BACKUP_DIR}/config_${DATE}.tar.gz" \
    config/ \
    .env.production \
    docker-compose.prod.yml \
    2>/dev/null || true

echo -e "${GREEN}✓ 配置文件备份完成${NC}"

# 3. 备份用户数据目录
echo "3. 备份用户数据..."
if [ -d "data" ]; then
    tar -czf "${BACKUP_DIR}/data_${DATE}.tar.gz" data/
    echo -e "${GREEN}✓ 用户数据备份完成${NC}"
fi

# 4. 创建完整备份包
echo "4. 创建完整备份包..."
cd "${BACKUP_DIR}"
tar -czf "vintagewisdom_full_${DATE}.tar.gz" \
    backup_${DATE}.db \
    config_${DATE}.tar.gz \
    data_${DATE}.tar.gz \
    2>/dev/null || true

# 清理临时文件
rm -f backup_${DATE}.db config_${DATE}.tar.gz data_${DATE}.tar.gz

echo -e "${GREEN}✓ 完整备份包已创建${NC}"

# 5. 清理旧备份
echo "5. 清理 ${KEEP_DAYS} 天前的备份..."
find "${BACKUP_DIR}" -name "vintagewisdom_full_*.tar.gz" -mtime +${KEEP_DAYS} -delete

# 6. 显示备份信息
BACKUP_SIZE=$(du -h "${BACKUP_DIR}/vintagewisdom_full_${DATE}.tar.gz" | cut -f1)
BACKUP_COUNT=$(ls -1 "${BACKUP_DIR}"/vintagewisdom_full_*.tar.gz 2>/dev/null | wc -l)

echo ""
echo "========================================="
echo "  备份完成"
echo "========================================="
echo ""
echo "备份文件: ${BACKUP_DIR}/vintagewisdom_full_${DATE}.tar.gz"
echo "备份大小: ${BACKUP_SIZE}"
echo "保留备份数: ${BACKUP_COUNT}"
echo ""
echo "恢复命令:"
echo "  ./scripts/restore.sh ${BACKUP_DIR}/vintagewisdom_full_${DATE}.tar.gz"
echo ""
