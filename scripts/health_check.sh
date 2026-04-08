#!/bin/bash

# VintageWisdom 健康检查脚本
# 使用方法: ./scripts/health_check.sh

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="${PROJECT_DIR}/logs/health_check.log"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 记录日志
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "${LOG_FILE}"
}

# 发送告警 (可以替换为邮件、Slack 等)
send_alert() {
    local message="$1"
    echo -e "${RED}[ALERT] ${message}${NC}"
    log "ALERT: ${message}"
    
    # 示例: 发送邮件告警
    # echo "${message}" | mail -s "VintageWisdom Health Alert" admin@example.com
    
    # 示例: 发送 Slack 告警
    # curl -X POST -H 'Content-type: application/json' \
    #   --data "{\"text\":\"${message}\"}" \
    #   YOUR_SLACK_WEBHOOK_URL
}

cd "${PROJECT_DIR}"

# 检查 Docker 服务
if ! docker compose -f docker-compose.prod.yml ps > /dev/null 2>&1; then
    send_alert "Docker Compose 服务异常"
    exit 1
fi

# 检查后端健康
BACKEND_HEALTH=$(docker compose -f docker-compose.prod.yml exec -T backend \
    curl -f -s http://localhost:8000/health 2>/dev/null || echo "failed")

if [ "${BACKEND_HEALTH}" == "failed" ]; then
    send_alert "后端服务健康检查失败"
    
    # 尝试重启后端
    log "尝试重启后端服务..."
    docker compose -f docker-compose.prod.yml restart backend
    sleep 10
    
    # 再次检查
    BACKEND_HEALTH=$(docker compose -f docker-compose.prod.yml exec -T backend \
        curl -f -s http://localhost:8000/health 2>/dev/null || echo "failed")
    
    if [ "${BACKEND_HEALTH}" == "failed" ]; then
        send_alert "后端服务重启后仍然失败"
        exit 1
    else
        log "后端服务重启成功"
    fi
else
    log "后端服务健康"
fi

# 检查前端
FRONTEND_HEALTH=$(docker compose -f docker-compose.prod.yml exec -T frontend \
    curl -f -s http://localhost:3000 2>/dev/null || echo "failed")

if [ "${FRONTEND_HEALTH}" == "failed" ]; then
    send_alert "前端服务健康检查失败"
    
    # 尝试重启前端
    log "尝试重启前端服务..."
    docker compose -f docker-compose.prod.yml restart frontend
    sleep 10
    
    # 再次检查
    FRONTEND_HEALTH=$(docker compose -f docker-compose.prod.yml exec -T frontend \
        curl -f -s http://localhost:3000 2>/dev/null || echo "failed")
    
    if [ "${FRONTEND_HEALTH}" == "failed" ]; then
        send_alert "前端服务重启后仍然失败"
        exit 1
    else
        log "前端服务重启成功"
    fi
else
    log "前端服务健康"
fi

# 检查 Redis
REDIS_HEALTH=$(docker compose -f docker-compose.prod.yml exec -T redis \
    redis-cli ping 2>/dev/null || echo "failed")

if [ "${REDIS_HEALTH}" != "PONG" ]; then
    send_alert "Redis 服务异常"
    docker compose -f docker-compose.prod.yml restart redis
    log "Redis 服务已重启"
fi

# 检查磁盘空间
DISK_USAGE=$(df -h "${PROJECT_DIR}" | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "${DISK_USAGE}" -gt 80 ]; then
    send_alert "磁盘空间不足: ${DISK_USAGE}% 已使用"
fi

# 检查内存使用
MEMORY_USAGE=$(free | awk 'NR==2 {printf "%.0f", $3/$2 * 100}')
if [ "${MEMORY_USAGE}" -gt 90 ]; then
    send_alert "内存使用过高: ${MEMORY_USAGE}%"
fi

# 检查数据库文件
if [ ! -f "${PROJECT_DIR}/data/vintagewisdom.db" ]; then
    send_alert "数据库文件不存在"
    exit 1
fi

log "所有健康检查通过"
echo -e "${GREEN}✓ 所有服务健康${NC}"
exit 0
