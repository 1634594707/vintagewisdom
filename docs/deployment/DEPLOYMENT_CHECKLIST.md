# VintageWisdom 部署检查清单

快速参考指南，确保部署过程顺利完成。

## 部署前准备

### 服务器准备
- [ ] 服务器已购买并可访问 (推荐: 2核4G, Ubuntu 22.04)
- [ ] SSH 密钥已配置
- [ ] 服务器防火墙已配置 (开放 22, 80, 443 端口)
- [ ] 域名已购买并解析到服务器 IP

### 域名配置
- [ ] 主域名 A 记录指向服务器 IP (example.com)
- [ ] API 子域名 A 记录指向服务器 IP (api.example.com)
- [ ] DNS 解析已生效 (使用 `nslookup` 或 `dig` 验证)

### 本地准备
- [ ] 代码已推送到 Git 仓库
- [ ] 环境变量已配置 (.env.production)
- [ ] 敏感信息已从代码中移除

---

## 服务器初始化

### 系统更新
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

- [ ] 系统已更新到最新版本

### 安装 Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo systemctl start docker
sudo systemctl enable docker
```

- [ ] Docker 已安装
- [ ] Docker 服务已启动
- [ ] 验证: `docker --version`

### 安装 Docker Compose
```bash
sudo apt install docker-compose-plugin -y
```

- [ ] Docker Compose 已安装
- [ ] 验证: `docker compose version`

### 创建部署用户
```bash
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG docker deploy
sudo passwd deploy
```

- [ ] deploy 用户已创建
- [ ] deploy 用户已加入 docker 组
- [ ] 可以使用 deploy 用户登录

---

## 代码部署

### 克隆项目
```bash
su - deploy
cd ~
git clone https://github.com/your-username/vintagewisdom.git
cd vintagewisdom
```

- [ ] 项目代码已克隆
- [ ] 当前在项目目录中

### 配置环境变量
```bash
cp .env.example .env.production
nano .env.production
```

需要配置的关键变量:
- [ ] `VW_ENV=production`
- [ ] `REDIS_PASSWORD` (生成强密码)
- [ ] `API_SECRET_KEY` (生成随机密钥)
- [ ] `DOMAIN` 和 `API_DOMAIN`

生成随机密码:
```bash
openssl rand -base64 32
```

### 创建必要目录
```bash
mkdir -p data logs nginx/conf.d nginx/ssl nginx/logs backups
```

- [ ] 目录结构已创建

---

## Docker 部署

### 构建镜像
```bash
docker compose -f docker-compose.prod.yml build
```

- [ ] 后端镜像构建成功
- [ ] 前端镜像构建成功
- [ ] 无构建错误

### 启动服务
```bash
docker compose -f docker-compose.prod.yml up -d
```

- [ ] 所有容器已启动
- [ ] 验证: `docker compose -f docker-compose.prod.yml ps`

### 初始化数据库
```bash
docker compose -f docker-compose.prod.yml exec backend python -m vintagewisdom init
```

- [ ] 数据库初始化成功
- [ ] 数据库文件已创建 (data/vintagewisdom.db)

---

## Nginx 配置

### 配置反向代理
```bash
nano nginx/conf.d/vintagewisdom.conf
```

- [ ] Nginx 配置文件已创建
- [ ] 域名已正确配置
- [ ] 代理规则已设置

### 测试配置
```bash
docker compose -f docker-compose.prod.yml exec nginx nginx -t
```

- [ ] Nginx 配置测试通过

---

## SSL 证书配置

### 方案 1: Let's Encrypt (推荐)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d example.com -d api.example.com
```

- [ ] Certbot 已安装
- [ ] SSL 证书已获取
- [ ] 证书自动续期已配置

### 方案 2: 手动上传证书

```bash
# 上传证书文件到 nginx/ssl/
scp fullchain.pem deploy@server:/home/deploy/vintagewisdom/nginx/ssl/
scp privkey.pem deploy@server:/home/deploy/vintagewisdom/nginx/ssl/
chmod 600 nginx/ssl/privkey.pem
```

- [ ] 证书文件已上传
- [ ] 证书权限已设置

### 重启 Nginx
```bash
docker compose -f docker-compose.prod.yml restart nginx
```

- [ ] Nginx 已重启
- [ ] HTTPS 访问正常

---

## 服务验证

### 健康检查

```bash
# 后端健康检查
curl http://localhost:8000/health

# 前端检查
curl http://localhost:3000

# HTTPS 检查
curl https://example.com
curl https://api.example.com/health
```

- [ ] 后端健康检查通过
- [ ] 前端可访问
- [ ] HTTPS 访问正常
- [ ] API 文档可访问 (https://api.example.com/docs)

### 查看日志
```bash
docker compose -f docker-compose.prod.yml logs -f
```

- [ ] 无错误日志
- [ ] 服务正常运行

---

## 备份配置

### 设置自动备份
```bash
chmod +x scripts/backup.sh
chmod +x scripts/restore.sh

# 添加到 crontab
crontab -e
# 添加: 0 2 * * * /home/deploy/vintagewisdom/scripts/backup.sh
```

- [ ] 备份脚本可执行
- [ ] 自动备份已配置
- [ ] 手动执行备份测试通过

### 测试备份
```bash
./scripts/backup.sh
```

- [ ] 备份文件已生成
- [ ] 备份文件完整

---

## 监控配置

### 配置日志轮转
```bash
sudo nano /etc/logrotate.d/vintagewisdom
```

添加配置:
```
/home/deploy/vintagewisdom/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 deploy deploy
}
```

- [ ] 日志轮转已配置

### 健康检查脚本
```bash
chmod +x scripts/health_check.sh

# 添加到 crontab
crontab -e
# 添加: */5 * * * * /home/deploy/vintagewisdom/scripts/health_check.sh
```

- [ ] 健康检查脚本已配置

---

## 安全加固

### 防火墙配置
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

- [ ] 防火墙已启用
- [ ] 必要端口已开放

### SSH 安全
编辑 `/etc/ssh/sshd_config`:
```
PermitRootLogin no
PasswordAuthentication no
```

```bash
sudo systemctl restart sshd
```

- [ ] Root 登录已禁用
- [ ] 密码登录已禁用 (仅密钥)

### 安装 fail2ban
```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

- [ ] fail2ban 已安装并运行

---

## 性能优化

### Redis 缓存
- [ ] Redis 已启动
- [ ] Redis 密码已设置
- [ ] 后端已连接 Redis

### 数据库优化
```bash
# 定期执行
docker compose -f docker-compose.prod.yml exec backend \
    sqlite3 /app/data/vintagewisdom.db "VACUUM;"
```

- [ ] 数据库优化计划已制定

---

## 最终验证

### 功能测试
- [ ] 用户可以访问前端页面
- [ ] 可以查看案例列表
- [ ] 可以添加新案例
- [ ] 可以执行决策查询
- [ ] 可以查看知识图谱
- [ ] API 文档可访问

### 性能测试
- [ ] 页面加载速度正常 (< 3秒)
- [ ] API 响应时间正常 (< 1秒)
- [ ] 无明显性能问题

### 安全测试
- [ ] HTTPS 证书有效
- [ ] HTTP 自动重定向到 HTTPS
- [ ] 安全头已配置
- [ ] 敏感端口未暴露

---

## 部署后任务

### 文档更新
- [ ] 更新 README 中的访问地址
- [ ] 记录部署配置和密码 (安全存储)
- [ ] 更新团队文档

### 监控设置
- [ ] 配置服务器监控 (可选: Prometheus, Grafana)
- [ ] 配置告警通知 (可选: Email, Slack)
- [ ] 配置日志聚合 (可选: ELK Stack)

### 备份验证
- [ ] 执行一次完整备份
- [ ] 测试恢复流程
- [ ] 确认备份自动化正常

---

## 常用命令参考

```bash
# 查看服务状态
docker compose -f docker-compose.prod.yml ps

# 查看日志
docker compose -f docker-compose.prod.yml logs -f [service]

# 重启服务
docker compose -f docker-compose.prod.yml restart [service]

# 停止所有服务
docker compose -f docker-compose.prod.yml down

# 更新部署
git pull origin main
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# 手动备份
./scripts/backup.sh

# 恢复备份
./scripts/restore.sh <backup_file>

# 查看资源使用
docker stats

# 进入容器
docker compose -f docker-compose.prod.yml exec backend bash
```

---

## 故障排查

如果遇到问题，按以下顺序检查:

1. **查看容器状态**: `docker compose -f docker-compose.prod.yml ps`
2. **查看日志**: `docker compose -f docker-compose.prod.yml logs [service]`
3. **检查端口**: `netstat -tulpn | grep -E ':(80|443|3000|8000)'`
4. **检查磁盘空间**: `df -h`
5. **检查内存**: `free -h`
6. **重启服务**: `docker compose -f docker-compose.prod.yml restart`

---

## 完成！

恭喜！如果所有检查项都已完成，你的 VintageWisdom 应用已成功部署到生产环境。

**访问地址:**
- 前端: https://example.com
- API: https://api.example.com
- API 文档: https://api.example.com/docs

**下一步:**
- 定期检查服务状态
- 监控日志和性能
- 定期更新系统和依赖
- 测试备份恢复流程

如有问题，请参考完整部署指南: `docs/deployment/DEPLOYMENT_GUIDE.md`
