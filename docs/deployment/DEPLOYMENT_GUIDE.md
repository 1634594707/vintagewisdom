# VintageWisdom 生产环境部署指南

本文档提供完整的生产环境部署流程，包括服务器配置、Docker 部署、域名配置、SSL 证书、监控和备份策略。

## 目录

1. [部署架构](#部署架构)
2. [前置准备](#前置准备)
3. [服务器配置](#服务器配置)
4. [Docker 部署](#docker-部署)
5. [Nginx 反向代理](#nginx-反向代理)
6. [SSL 证书配置](#ssl-证书配置)
7. [环境变量配置](#环境变量配置)
8. [数据库迁移](#数据库迁移)
9. [监控与日志](#监控与日志)
10. [备份策略](#备份策略)
11. [CI/CD 自动化](#cicd-自动化)
12. [故障排查](#故障排查)

---

## 部署架构

```
                    ┌─────────────────┐
                    │   用户浏览器     │
                    └────────┬────────┘
                             │ HTTPS
                    ┌────────▼────────┐
                    │  Nginx (443)    │
                    │  SSL 终止        │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼────────┐ ┌──▼──────┐ ┌────▼─────┐
     │  Next.js (3000) │ │ FastAPI │ │  静态资源 │
     │    前端服务      │ │  (8000) │ │          │
     └─────────────────┘ └────┬────┘ └──────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
     ┌────────▼────────┐ ┌───▼────┐ ┌───────▼────────┐
     │  SQLite DB      │ │ Redis  │ │    Qdrant      │
     │  (主数据库)      │ │ (缓存) │ │  (向量存储)     │
     └─────────────────┘ └────────┘ └────────────────┘
```

---

## 前置准备

### 1. 服务器要求

**最低配置：**
- CPU: 2 核
- 内存: 4GB
- 硬盘: 20GB SSD
- 操作系统: Ubuntu 22.04 LTS / CentOS 8+ / Debian 11+

**推荐配置：**
- CPU: 4 核
- 内存: 8GB
- 硬盘: 50GB SSD
- 操作系统: Ubuntu 22.04 LTS

### 2. 域名准备

- 主域名: `example.com`
- API 子域名: `api.example.com`
- 前端子域名: `app.example.com` (可选)

### 3. 必需软件

- Docker >= 24.0
- Docker Compose >= 2.20
- Git
- Nginx (如果不用 Docker 部署 Nginx)

---

## 服务器配置

### 1. 连接服务器

```bash
ssh root@your-server-ip
```

### 2. 更新系统

```bash
# Ubuntu/Debian
apt update && apt upgrade -y

# CentOS/RHEL
yum update -y
```

### 3. 安装 Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 启动 Docker
systemctl start docker
systemctl enable docker

# 安装 Docker Compose
apt install docker-compose-plugin -y
```

### 4. 创建部署用户

```bash
# 创建用户
useradd -m -s /bin/bash deploy
usermod -aG docker deploy

# 设置密码
passwd deploy

# 切换到 deploy 用户
su - deploy
```

### 5. 配置防火墙

```bash
# Ubuntu (UFW)
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable

# CentOS (firewalld)
firewall-cmd --permanent --add-service=ssh
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

---

## Docker 部署

### 1. 克隆项目

```bash
cd /home/deploy
git clone https://github.com/your-username/vintagewisdom.git
cd vintagewisdom
```

### 2. 创建生产环境 Docker Compose 文件

创建 `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  # 后端 API
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: vw_backend
    restart: unless-stopped
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      - VW_ENV=production
      - VW_DATA_DIR=/app/data
      - VW_LOG_LEVEL=INFO
    env_file:
      - .env.production
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./logs:/app/logs
    depends_on:
      - redis
      - qdrant
    networks:
      - vw_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 前端
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - NEXT_PUBLIC_API_BASE=https://api.example.com
    container_name: vw_frontend
    restart: unless-stopped
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      - NODE_ENV=production
    networks:
      - vw_network
    depends_on:
      - backend

  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: vw_redis
    restart: unless-stopped
    ports:
      - "127.0.0.1:6379:6379"
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - vw_network

  # Qdrant 向量数据库
  qdrant:
    image: qdrant/qdrant:v1.9.3
    container_name: vw_qdrant
    restart: unless-stopped
    ports:
      - "127.0.0.1:6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    networks:
      - vw_network

  # Nginx 反向代理
  nginx:
    image: nginx:alpine
    container_name: vw_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/logs:/var/log/nginx
    depends_on:
      - backend
      - frontend
    networks:
      - vw_network

volumes:
  redis_data:
  qdrant_data:

networks:
  vw_network:
    driver: bridge
```

### 3. 创建后端 Dockerfile

创建 `Dockerfile.backend`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装 uv 和 Python 依赖
RUN pip install --no-cache-dir uv && \
    uv sync --extra web --extra ingest --extra graphrag

# 复制应用代码
COPY src/ ./src/
COPY config/ ./config/

# 创建数据目录
RUN mkdir -p /app/data /app/logs

# 初始化数据库
RUN python -m vintagewisdom init

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python", "-m", "uvicorn", "vintagewisdom.web.app:create_app", \
     "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

### 4. 创建前端 Dockerfile

创建 `frontend/Dockerfile`:

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# 安装 pnpm
RUN npm install -g pnpm

# 复制依赖文件
COPY package.json pnpm-lock.yaml ./

# 安装依赖
RUN pnpm install --frozen-lockfile

# 复制源代码
COPY . .

# 构建应用
ARG NEXT_PUBLIC_API_BASE
ENV NEXT_PUBLIC_API_BASE=${NEXT_PUBLIC_API_BASE}
RUN pnpm build

# 生产镜像
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# 复制必要文件
COPY --from=builder /app/next.config.ts ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
```

### 5. 配置环境变量

创建 `.env.production`:

```bash
# 应用配置
VW_ENV=production
VW_DATA_DIR=/app/data
VW_LOG_LEVEL=INFO

# Redis 配置
REDIS_PASSWORD=your_strong_redis_password_here

# API 密钥 (如果使用)
API_SECRET_KEY=your_secret_key_here

# AI 配置 (可选)
OLLAMA_BASE_URL=http://your-ollama-server:11434
OPENAI_API_KEY=your_openai_key_here

# 数据库备份
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"  # 每天凌晨 2 点
```

### 6. 启动服务

```bash
# 构建镜像
docker compose -f docker-compose.prod.yml build

# 启动服务
docker compose -f docker-compose.prod.yml up -d

# 查看日志
docker compose -f docker-compose.prod.yml logs -f

# 查看服务状态
docker compose -f docker-compose.prod.yml ps
```

---

## Nginx 反向代理

### 1. 创建 Nginx 配置目录

```bash
mkdir -p nginx/conf.d nginx/ssl nginx/logs
```

### 2. 创建主配置文件

创建 `nginx/nginx.conf`:

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml font/truetype font/opentype 
               application/vnd.ms-fontobject image/svg+xml;

    # 包含站点配置
    include /etc/nginx/conf.d/*.conf;
}
```

### 3. 创建站点配置

创建 `nginx/conf.d/vintagewisdom.conf`:

```nginx
# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name example.com api.example.com;
    
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
    server_name example.com;

    # SSL 证书
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 日志
    access_log /var/log/nginx/frontend_access.log;
    error_log /var/log/nginx/frontend_error.log;

    # 代理到前端
    location / {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}

# API 服务
server {
    listen 443 ssl http2;
    server_name api.example.com;

    # SSL 证书
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;

    # 日志
    access_log /var/log/nginx/api_access.log;
    error_log /var/log/nginx/api_error.log;

    # 限流
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req zone=api_limit burst=20 nodelay;

    # 代理到后端 API
    location / {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 健康检查
    location /health {
        proxy_pass http://backend:8000/health;
        access_log off;
    }
}
```

---

## SSL 证书配置

### 方案 1: Let's Encrypt (推荐，免费)

```bash
# 安装 Certbot
apt install certbot python3-certbot-nginx -y

# 获取证书
certbot --nginx -d example.com -d api.example.com

# 自动续期
certbot renew --dry-run

# 添加自动续期任务
echo "0 3 * * * certbot renew --quiet" | crontab -
```

### 方案 2: 手动配置证书

```bash
# 将证书文件复制到 nginx/ssl 目录
cp fullchain.pem nginx/ssl/
cp privkey.pem nginx/ssl/

# 设置权限
chmod 600 nginx/ssl/privkey.pem
```

---

## 环境变量配置

### 1. 前端环境变量

修改 `frontend/.env.production`:

```bash
NEXT_PUBLIC_API_BASE=https://api.example.com
NODE_ENV=production
```

### 2. 后端环境变量

确保 `.env.production` 包含所有必要配置。

---

## 数据库迁移

### 1. 初始化数据库

```bash
docker compose -f docker-compose.prod.yml exec backend python -m vintagewisdom init
```

### 2. 导入初始数据 (可选)

```bash
# 复制数据文件到容器
docker cp examples/fintech_cases.json vw_backend:/app/

# 导入数据
docker compose -f docker-compose.prod.yml exec backend \
    python -m vintagewisdom import-json --file /app/fintech_cases.json
```

---

## 监控与日志

### 1. 查看服务日志

```bash
# 所有服务
docker compose -f docker-compose.prod.yml logs -f

# 特定服务
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
```

### 2. 配置日志轮转

创建 `/etc/logrotate.d/vintagewisdom`:

```
/home/deploy/vintagewisdom/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 deploy deploy
    sharedscripts
    postrotate
        docker compose -f /home/deploy/vintagewisdom/docker-compose.prod.yml \
            exec backend kill -USR1 1
    endscript
}
```

### 3. 健康检查脚本

创建 `scripts/health_check.sh`:

```bash
#!/bin/bash

# 检查后端健康
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "Backend health check failed"
    # 发送告警通知
    exit 1
fi

# 检查前端
if ! curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "Frontend health check failed"
    exit 1
fi

echo "All services healthy"
```

添加到 crontab:

```bash
*/5 * * * * /home/deploy/vintagewisdom/scripts/health_check.sh
```

---

## 备份策略

### 1. 创建备份脚本

创建 `scripts/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/home/deploy/backups"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/home/deploy/vintagewisdom"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
docker compose -f $PROJECT_DIR/docker-compose.prod.yml exec -T backend \
    sqlite3 /app/data/vintagewisdom.db ".backup /app/data/backup_$DATE.db"

# 复制备份文件
docker cp vw_backend:/app/data/backup_$DATE.db $BACKUP_DIR/

# 压缩备份
cd $BACKUP_DIR
tar -czf vintagewisdom_backup_$DATE.tar.gz backup_$DATE.db
rm backup_$DATE.db

# 删除 30 天前的备份
find $BACKUP_DIR -name "vintagewisdom_backup_*.tar.gz" -mtime +30 -delete

echo "Backup completed: vintagewisdom_backup_$DATE.tar.gz"
```

### 2. 设置自动备份

```bash
chmod +x scripts/backup.sh

# 添加到 crontab (每天凌晨 2 点)
echo "0 2 * * * /home/deploy/vintagewisdom/scripts/backup.sh" | crontab -
```

### 3. 恢复备份

```bash
# 解压备份
tar -xzf vintagewisdom_backup_YYYYMMDD_HHMMSS.tar.gz

# 停止服务
docker compose -f docker-compose.prod.yml stop backend

# 恢复数据库
docker cp backup_YYYYMMDD_HHMMSS.db vw_backend:/app/data/vintagewisdom.db

# 重启服务
docker compose -f docker-compose.prod.yml start backend
```

---

## CI/CD 自动化

### GitHub Actions 示例

创建 `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /home/deploy/vintagewisdom
            git pull origin main
            docker compose -f docker-compose.prod.yml build
            docker compose -f docker-compose.prod.yml up -d
            docker compose -f docker-compose.prod.yml exec backend python -m vintagewisdom init
```

---

## 故障排查

### 1. 服务无法启动

```bash
# 查看容器状态
docker compose -f docker-compose.prod.yml ps

# 查看详细日志
docker compose -f docker-compose.prod.yml logs backend

# 检查端口占用
netstat -tulpn | grep -E ':(80|443|3000|8000)'
```

### 2. 数据库连接失败

```bash
# 进入容器检查
docker compose -f docker-compose.prod.yml exec backend bash
ls -la /app/data/
```

### 3. Nginx 配置错误

```bash
# 测试配置
docker compose -f docker-compose.prod.yml exec nginx nginx -t

# 重新加载配置
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### 4. 性能问题

```bash
# 查看资源使用
docker stats

# 查看容器日志大小
docker compose -f docker-compose.prod.yml exec backend du -sh /app/logs/
```

---

## 安全加固

### 1. 配置防火墙

```bash
# 只允许必要端口
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 2. 禁用 root SSH 登录

编辑 `/etc/ssh/sshd_config`:

```
PermitRootLogin no
PasswordAuthentication no
```

重启 SSH:

```bash
systemctl restart sshd
```

### 3. 配置 fail2ban

```bash
apt install fail2ban -y
systemctl enable fail2ban
systemctl start fail2ban
```

---

## 性能优化

### 1. 启用 Redis 缓存

确保 Redis 配置正确，后端使用缓存。

### 2. 配置 CDN (可选)

使用 Cloudflare 或其他 CDN 服务加速静态资源。

### 3. 数据库优化

```bash
# 定期清理和优化
docker compose -f docker-compose.prod.yml exec backend \
    sqlite3 /app/data/vintagewisdom.db "VACUUM;"
```

---

## 更新部署

### 1. 拉取最新代码

```bash
cd /home/deploy/vintagewisdom
git pull origin main
```

### 2. 重新构建并部署

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### 3. 零停机更新 (可选)

使用 Docker Swarm 或 Kubernetes 实现零停机部署。

---

## 总结

完成以上步骤后，你的 VintageWisdom 应用将：

✅ 运行在生产环境
✅ 使用 HTTPS 加密
✅ 配置反向代理和负载均衡
✅ 自动备份数据
✅ 监控服务健康状态
✅ 日志轮转和管理
✅ 安全加固

如有问题，请查看日志或参考故障排查章节。
