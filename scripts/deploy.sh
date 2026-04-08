#!/bin/bash

# VintageWisdom 一键部署脚本
# 使用方法: ./scripts/deploy.sh

set -e

echo "========================================="
echo "  VintageWisdom 生产环境部署脚本"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为 root 用户
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}请不要使用 root 用户运行此脚本${NC}"
    echo "建议使用普通用户，并确保该用户在 docker 组中"
    exit 1
fi

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker 未安装，请先安装 Docker${NC}"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! docker compose version &> /dev/null; then
    echo -e "${RED}Docker Compose 未安装，请先安装 Docker Compose${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker 环境检查通过${NC}"
echo ""

# 询问部署模式
echo "请选择部署模式:"
echo "1) 完整部署 (包括 Nginx)"
echo "2) 仅应用 (不包括 Nginx，使用外部反向代理)"
read -p "请输入选项 [1-2]: " DEPLOY_MODE

# 询问域名
read -p "请输入主域名 (例如: example.com): " DOMAIN
read -p "请输入 API 子域名 (例如: api.example.com): " API_DOMAIN

# 询问是否配置 SSL
read -p "是否配置 SSL 证书? [y/N]: " SETUP_SSL

# 生成随机密码
REDIS_PASSWORD=$(openssl rand -base64 32)
API_SECRET=$(openssl rand -base64 32)

echo ""
echo -e "${YELLOW}开始部署...${NC}"
echo ""

# 1. 创建必要的目录
echo "1. 创建目录结构..."
mkdir -p data logs nginx/conf.d nginx/ssl nginx/logs backups

# 2. 创建环境变量文件
echo "2. 生成环境变量配置..."
cat > .env.production << EOF
# 应用配置
VW_ENV=production
VW_DATA_DIR=/app/data
VW_LOG_LEVEL=INFO

# Redis 配置
REDIS_PASSWORD=${REDIS_PASSWORD}

# API 密钥
API_SECRET_KEY=${API_SECRET}

# 备份配置
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"

# 域名配置
DOMAIN=${DOMAIN}
API_DOMAIN=${API_DOMAIN}
EOF

echo -e "${GREEN}✓ 环境变量配置已生成${NC}"

# 3. 创建 Nginx 配置
if [ "$DEPLOY_MODE" == "1" ]; then
    echo "3. 生成 Nginx 配置..."
    
    # 创建基础配置
    cat > nginx/conf.d/vintagewisdom.conf << 'EOF'
# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name DOMAIN API_DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# 前端服务
server {
    listen 443 ssl http2;
    server_name DOMAIN;

    # SSL 证书路径
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 安全头
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    location / {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# API 服务
server {
    listen 443 ssl http2;
    server_name API_DOMAIN;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://backend:8000/health;
        access_log off;
    }
}
EOF

    # 替换域名
    sed -i "s/DOMAIN/${DOMAIN}/g" nginx/conf.d/vintagewisdom.conf
    sed -i "s/API_DOMAIN/${API_DOMAIN}/g" nginx/conf.d/vintagewisdom.conf
    
    echo -e "${GREEN}✓ Nginx 配置已生成${NC}"
fi

# 4. 构建和启动服务
echo "4. 构建 Docker 镜像..."
docker compose -f docker-compose.prod.yml build

echo "5. 启动服务..."
docker compose -f docker-compose.prod.yml up -d

# 等待服务启动
echo "6. 等待服务启动..."
sleep 10

# 7. 初始化数据库
echo "7. 初始化数据库..."
docker compose -f docker-compose.prod.yml exec -T backend python -m vintagewisdom init

# 8. 配置 SSL (如果需要)
if [ "$SETUP_SSL" == "y" ] || [ "$SETUP_SSL" == "Y" ]; then
    echo "8. 配置 SSL 证书..."
    
    if command -v certbot &> /dev/null; then
        echo "使用 Certbot 获取 Let's Encrypt 证书..."
        sudo certbot certonly --webroot -w /var/www/certbot \
            -d ${DOMAIN} -d ${API_DOMAIN} \
            --email admin@${DOMAIN} --agree-tos --no-eff-email
        
        # 复制证书到 nginx 目录
        sudo cp /etc/letsencrypt/live/${DOMAIN}/fullchain.pem nginx/ssl/
        sudo cp /etc/letsencrypt/live/${DOMAIN}/privkey.pem nginx/ssl/
        sudo chown $(whoami):$(whoami) nginx/ssl/*.pem
        
        # 重启 Nginx
        docker compose -f docker-compose.prod.yml restart nginx
        
        echo -e "${GREEN}✓ SSL 证书配置完成${NC}"
    else
        echo -e "${YELLOW}Certbot 未安装，请手动配置 SSL 证书${NC}"
        echo "证书文件应放置在: nginx/ssl/fullchain.pem 和 nginx/ssl/privkey.pem"
    fi
fi

# 9. 设置自动备份
echo "9. 配置自动备份..."
chmod +x scripts/backup.sh

# 添加到 crontab (如果还没有)
(crontab -l 2>/dev/null | grep -v "backup.sh"; echo "0 2 * * * $(pwd)/scripts/backup.sh") | crontab -

echo -e "${GREEN}✓ 自动备份已配置 (每天凌晨 2 点)${NC}"

# 10. 健康检查
echo "10. 执行健康检查..."
sleep 5

BACKEND_HEALTH=$(docker compose -f docker-compose.prod.yml exec -T backend curl -f http://localhost:8000/health 2>/dev/null || echo "failed")
FRONTEND_HEALTH=$(docker compose -f docker-compose.prod.yml exec -T frontend curl -f http://localhost:3000 2>/dev/null || echo "failed")

echo ""
echo "========================================="
echo "  部署完成！"
echo "========================================="
echo ""
echo -e "后端健康状态: ${BACKEND_HEALTH}"
echo -e "前端健康状态: ${FRONTEND_HEALTH}"
echo ""
echo "访问地址:"
echo "  前端: https://${DOMAIN}"
echo "  API:  https://${API_DOMAIN}"
echo "  API 文档: https://${API_DOMAIN}/docs"
echo ""
echo "重要信息 (请妥善保存):"
echo "  Redis 密码: ${REDIS_PASSWORD}"
echo "  API 密钥: ${API_SECRET}"
echo ""
echo "常用命令:"
echo "  查看日志: docker compose -f docker-compose.prod.yml logs -f"
echo "  重启服务: docker compose -f docker-compose.prod.yml restart"
echo "  停止服务: docker compose -f docker-compose.prod.yml down"
echo "  手动备份: ./scripts/backup.sh"
echo ""
echo -e "${GREEN}部署成功！${NC}"
