# VintageWisdom

VintageWisdom 是一个基于历史案例的个人决策支持系统，提供：

- Python CLI
- FastAPI Web API
- Next.js 前端工作台
- CSV / JSON / PDF / DOCX 导入
- 案例图谱与知识图谱展示
- 可切换的 AI 配置

当前仓库已经收口为 `1.0.0` 发布版，示例素材、过程文档、失效脚本和未使用前端残留已移除。

## 目录

- `src/vintagewisdom/`: 后端与 CLI
- `frontend/`: Next.js 前端
- `config/`: 默认配置
- `data/`: 本地数据目录
- `tests/`: 后端测试
- `docs/`: 发布相关文档

## 环境要求

- Python `>= 3.10`
- Node.js `>= 20`
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

## 初始化数据

```bash
python -m vintagewisdom init
```

或：

```bash
vw init
```

## 启动后端 API

```bash
python -m uvicorn vintagewisdom.web.app:create_app --factory --host 127.0.0.1 --port 8000 --reload
```

启动后可访问：

- API 文档: `http://127.0.0.1:8000/docs`
- 健康检查: `http://127.0.0.1:8000/health`

## 启动前端

```bash
cd frontend
pnpm install
pnpm dev
```

默认前端地址：

- `http://127.0.0.1:3000`

如果后端不在 `127.0.0.1:8000`：

```powershell
$env:NEXT_PUBLIC_API_BASE = "http://127.0.0.1:8000"
pnpm dev
```

## 常用命令

后端质量检查：

```bash
pytest
ruff check .
mypy src/
```

前端质量检查：

```bash
cd frontend
pnpm install
pnpm lint
pnpm build
```

## CLI 示例

```bash
vw stats
vw query "Should I accept this offer?"
vw import-csv --file ./cases.csv
vw ingest-doc --file ./docs/a.pdf --type auto
```

## 可选服务

仓库内的 `docker-compose.yml` 仅用于启动可选依赖：

- Redis
- Qdrant

```bash
docker compose up -d
```

这不是完整生产部署编排；完整发布说明见 `docs/`。

## 发布说明

- 当前版本：`1.0.0`
- 已删除仓库内示例数据与模板文件
- 已删除默认 `demo` 插件
- 已删除未使用的 ReactFlow 旧图谱实现与默认静态资源
- 已移除与当前仓库不一致的伪生产脚本

## 文档

- `docs/README.md`
- `docs/api/API_SPECIFICATION.md`
- `docs/deployment/DEPLOYMENT_GUIDE.md`
- `docs/architecture/ARCHITECTURE.md`
