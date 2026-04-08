# VintageWisdom

VintageWisdom 是一个基于历史案例的轻量决策支持系统。当前仓库已经按“可上线、易维护、尽量精简”的目标完成收口，只保留后端核心、前端工作台、必要配置与部署文档。

## 仓库保留内容

- `src/vintagewisdom/`: Python 后端、CLI、API 与核心服务
- `frontend/`: Next.js 前端
- `config/default.yaml`: 默认发布配置
- `docs/`: API、架构与部署说明
- `tests/`: 核心回归测试

本地运行数据、私有配置、缓存文件与生成产物都不会提交到 git。

## 环境要求

- Python `>=3.10`
- Node.js `>=20`
- `pnpm`
- 推荐使用 `uv`

## 安装后端

```bash
uv sync --extra dev --extra web --extra ingest
```

如果不用 `uv`：

```bash
pip install -e ".[dev,web,ingest]"
```

## 本地覆盖配置

`config/user.yaml` 只用于机器私有配置，例如 API Key、自定义路径等。这个文件已被 git 忽略，不应该提交。

最小示例：

```yaml
ai:
  provider: api
  model: your-model
  api_base: https://your-api-host/v1
  api_key: your-secret
```

## 初始化数据

```bash
python -m vintagewisdom init
```

或：

```bash
vw init
```

## 启动 API

```bash
python -m uvicorn vintagewisdom.web.app:create_app --factory --host 0.0.0.0 --port 8000
```

常用地址：

- API 文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/health`

## 启动前端

```bash
cd frontend
pnpm install
pnpm build
pnpm start
```

本地开发可用：

```bash
cd frontend
pnpm dev
```

如果后端不在 `http://127.0.0.1:8000`，先设置：

```powershell
$env:NEXT_PUBLIC_API_BASE = "http://127.0.0.1:8000"
```

## 质量检查

后端：

```bash
pytest
ruff check .
```

前端：

```bash
cd frontend
pnpm lint
pnpm build
```

## 发布说明

- 默认配置已经收敛为最小可运行版本，启动时不依赖 Redis、Neo4j、Qdrant。
- 运行期数据会写入 `data/`，但不会进入仓库。
- 可选能力可以后续通过 `config/user.yaml` 再开启。

详细说明见：

- `docs/deployment/DEPLOYMENT_GUIDE.md`
- `docs/api/API_SPECIFICATION.md`
- `docs/architecture/ARCHITECTURE.md`
