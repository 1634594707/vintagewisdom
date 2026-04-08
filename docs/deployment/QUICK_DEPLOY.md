# VintageWisdom 快速部署指南

5 分钟快速部署到生产环境。

## 前提条件

- 一台 Linux 服务器 (Ubuntu 22.04 推荐)
- 域名已解析到服务器 IP
- 服务器已安装 Docker 和 Docker Compose

## 一键部署

### 1. 连接服务器

```bash
ssh deploy@your-server-ip
```

### 2. 克隆项目

```bash
cd ~
git clone https://github.com/your-username/vintagewisdom.git
cd vintagewisdom
```

### 3. 运行部署脚本

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

按提示输入:
- 部署模式 (选择 1: 完整部署)
- 主域名 (例如: example.com)
- API 子域名 (例如: api.example.com)
- 是否配置 SSL (输入 y)

### 4. 等待部署完成

脚本会自动:
- ✅ 创建必要的目录
- ✅ 生成环境变量配置
- ✅ 配置 Nginx 反向代理
- ✅ 构建 Docker 镜像
- ✅ 启动所有服务
- ✅ 初始化数据库
- ✅ 配置 SSL 证书
- ✅ 设置自动备份

### 5. 访问应用

部署完成后，访问:
- 前端: https://example.com
- API: https://api.example.com
- API 文档: https://api.example.com/docs

---

## 手动部署 (分步骤)

如果你想更细粒度地控制部署过程:

### 步骤 1: 准备环境

```bash
# 创建目录
mkdir -p data logs nginx/conf.d nginx/ssl backups

# 复制环境变量模板
cp .env.example .env.production

# 编辑环境变量
nano .env.production
```

### 步骤 2: 配置 Nginx

```bash
# 复制 Nginx 配置模板
cp docs/deployment/nginx.conf.example nginx/conf.d/vintagewisdom.conf

# 修改域名
sed -i 's/example.com/your-domain.com/g' nginx/conf.d/vintagewisdom.conf
```

### 步骤 3: 构建和启动

```bash
# 构建镜像
docker compose -f docker-compose.prod.yml build

# 启动服务
docker compose -f docker-compose.prod.yml up -d

# 初始化数据库
docker compose -f docker-compose.prod.yml exec backend python -m vintagewisdom init
```

### 步骤 4: 配置 SSL

```bash
# 使用 Let's Encrypt
sudo certbot --nginx -d your-domain.com -d api.your-domain.com

# 或手动上传证书
cp fullchain.pem nginx/ssl/
cp privkey.pem nginx/ssl/
docker compose -f docker-compose.prod.yml restart nginx
```

### 步骤 5: 配置备份

```bash
chmod +x scripts/backup.sh

# 添加到 crontab
crontab -e
# 添加: 0 2 * * * /home/deploy/vintagewisdom/scripts/backup.sh
```

---

## 验证部署

### 检查服务状态

```bash
docker compose -f docker-compose.prod.yml ps
```

应该看到所有服务都是 "Up" 状态。

### 健康检查

```bash
# 后端
curl http://localhost:8000/health

# 前端
curl http://localhost:3000

# HTTPS
curl https://your-domain.com
curl https://api.your-domain.com/health
```

### 查看日志

```bash
docker compose -f docker-compose.prod.yml logs -f
```

---

## 常见问题

### 1. 端口被占用

```bash
# 查看端口占用
netstat -tulpn | grep -E ':(80|443|3000|8000)'

# 停止占用端口的服务
sudo systemctl stop apache2  # 如果是 Apache
sudo systemctl stop nginx    # 如果是系统 Nginx
```

### 2. Docker 权限问题

```bash
# 将当前用户加入 docker 组
sudo usermod -aG docker $USER

# 重新登录使生效
exit
ssh deploy@your-server-ip
```

### 3. SSL 证书获取失败

确保:
- 域名已正确解析到服务器 IP
- 防火墙已开放 80 和 443 端口
- Nginx 已启动

```bash
# 检查域名解析
nslookup your-domain.com

# 检查防火墙
sudo ufw status

# 重试获取证书
sudo certbot --nginx -d your-domain.com -d api.your-domain.com
```

### 4. 服务无法启动

```bash
# 查看详细日志
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs frontend

# 检查配置文件
docker compose -f docker-compose.prod.yml config

# 重新构建
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
```

---

## 更新部署

### 拉取最新代码

```bash
cd ~/vintagewisdom
git pull origin main
```

### 重新构建和部署

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### 零停机更新 (可选)

```bash
# 使用滚动更新
docker compose -f docker-compose.prod.yml up -d --no-deps --build backend
docker compose -f docker-compose.prod.yml up -d --no-deps --build frontend
```

---

## 备份和恢复

### 手动备份

```bash
./scripts/backup.sh
```

备份文件保存在: `~/backups/vintagewisdom/`

### 恢复备份

```bash
./scripts/restore.sh ~/backups/vintagewisdom/vintagewisdom_full_YYYYMMDD_HHMMSS.tar.gz
```

---

## 卸载

如果需要完全卸载:

```bash
# 停止并删除容器
docker compose -f docker-compose.prod.yml down -v

# 删除镜像
docker rmi $(docker images | grep vintagewisdom | awk '{print $3}')

# 删除项目目录 (谨慎操作！)
cd ~
rm -rf vintagewisdom
```

---

## 下一步

- 📖 查看完整部署指南: [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- ✅ 使用部署检查清单: [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)
- 🔧 配置监控和告警
- 📊 设置性能监控
- 🔐 定期更新系统和依赖

---

## 获取帮助

- 查看日志: `docker compose -f docker-compose.prod.yml logs -f`
- 查看文档: `docs/` 目录
- 提交 Issue: GitHub Issues
- 联系支持: support@example.com

---

**祝部署顺利！** 🚀
