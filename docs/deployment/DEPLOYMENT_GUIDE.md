# Deployment Guide

本仓库当前提供的是“应用本体 + 可选依赖服务”的发布形态：

- 后端：FastAPI
- 前端：Next.js
- 可选服务：Redis、Qdrant

仓库里没有完整的生产 `docker-compose.prod.yml`，因此发布方式以“手动进程管理”或你自己的容器编排为准。下面是当前仓库可直接落地的最小部署方案。

## 1. 服务器准备

- Linux 主机
- Python 3.10+
- Node.js 20+
- `pnpm`
- 可选：`uv`
- 可选：Docker（如果要启动 Redis/Qdrant）

## 2. 拉取代码

```bash
git clone <your-repo-url>
cd VintageWisdom
```

## 3. 安装后端依赖

```bash
uv sync --extra web --extra ingest
```

或：

```bash
pip install -e ".[web,ingest]"
```

## 4. 初始化数据

```bash
python -m vintagewisdom init
```

## 5. 启动可选依赖

如果你需要 Redis 或 Qdrant：

```bash
docker compose up -d
```

`docker-compose.yml` 只包含这两个服务，不会自动启动前后端。

## 6. 启动后端

开发/单机部署可直接运行：

```bash
python -m uvicorn vintagewisdom.web.app:create_app --factory --host 0.0.0.0 --port 8000
```

生产环境建议自行使用 `systemd`、`supervisor` 或容器平台托管该命令。

## 7. 构建并启动前端

```bash
cd frontend
pnpm install
pnpm build
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000 pnpm start
```

如果前后端不在同一台机器，请把 `NEXT_PUBLIC_API_BASE` 指向实际 API 地址。

## 8. 反向代理

建议使用 Nginx 或 Caddy：

- 前端代理到 `3000`
- `/api` 或独立域名代理到 `8000`
- 开启 HTTPS

当前仓库不再附带示例反向代理配置文件，建议你在部署环境中自行维护 Nginx 或 Caddy 配置。

## 9. 发布检查

上线前至少确认：

- `GET /health` 返回 `{"status":"ok"}`
- `GET /docs` 可打开
- 前端首页可加载
- 案例列表、查询、导入页面可访问
- `pnpm build` 成功
- `pytest` 成功

## 10. 当前边界

当前发布版没有内置这些能力：

- 一键生产部署脚本
- 完整生产 Docker 编排
- 自动备份/恢复脚本
- 自动健康巡检脚本

如果需要这些能力，建议在你自己的部署仓库或运维层补充，而不是继续依赖当前仓库中旧的失效脚本。
