# VintageWisdom

VintageWisdom 是一个面向历史案例复用的个人决策支持系统。

它把案例沉淀、相似检索、决策查询、知识图谱和 AI 辅助分析放在同一个工作流里，方便你把过去的经验真正变成可复用的判断资产。

## 当前能力

- 本地保存案例、决策记录与导入任务
- 提供 FastAPI Web API
- 提供 Next.js 前端工作台
- 支持 CSV、JSON、PDF、DOCX 导入
- 支持异步 JSON 导入和任务进度查询
- 支持案例图谱 / 知识图谱展示
- 支持 AI 配置切换，本地 Ollama 和兼容 OpenAI 的远程接口都可接入

## 技术栈

- 后端: Python 3.10+, FastAPI, Pydantic
- 前端: Next.js 16, React 19, Tailwind CSS 4, Sigma.js
- 存储: SQLite
- 可选能力: `pypdf`, `python-docx`, `neo4j`, `redis`, `qdrant`

## 环境要求

- Python `>= 3.10`
- Node.js `>= 20`
- `pnpm`
- 推荐使用 `uv`

## 快速启动

### 1. 安装后端依赖

推荐:

```bash
uv sync --extra dev --extra web --extra ingest
```

如果你不用 `uv`:

```bash
pip install -e ".[dev,web,ingest]"
```

### 2. 初始化本地数据库

```bash
python -m vintagewisdom init
```

或者:

```bash
vw init
```

### 3. 启动后端 API

```bash
python -m uvicorn vintagewisdom.web.app:create_app --factory --host 127.0.0.1 --port 8000 --reload
```

启动后访问:

- API 文档: `http://127.0.0.1:8000/docs`
- 健康检查: `http://127.0.0.1:8000/health`

### 4. 启动前端

```bash
cd frontend
pnpm install
pnpm dev
```

说明:

- `pnpm dev` 现在默认走 `webpack`，用于规避 Windows 下 Turbopack 偶发的资源不足 panic
- 如果你想手动试 Turbopack，可以用 `pnpm run dev:turbo`

默认访问:

- 前端首页: `http://127.0.0.1:3000`
- 决策查询: `http://127.0.0.1:3000/query`
- 知识图谱: `http://127.0.0.1:3000/graph`

如果后端不是跑在 `127.0.0.1:8000`，先设置环境变量:

```bash
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
```

PowerShell:

```powershell
$env:NEXT_PUBLIC_API_BASE = "http://127.0.0.1:8000"
pnpm dev
```

## 推荐启动顺序

开发时建议按下面顺序启动:

1. 安装 Python 依赖
2. 执行 `vw init`
3. 启动后端 API
4. 进入 `frontend/` 启动前端
5. 打开 `http://127.0.0.1:3000`

## 只启动后端

如果你只想先验证 API:

```bash
uv sync --extra web --extra ingest
python -m vintagewisdom init
python -m uvicorn vintagewisdom.web.app:create_app --factory --host 127.0.0.1 --port 8000 --reload
```

## 只使用 CLI

项目也支持命令行操作。

### 查询

```bash
vw query "Should I accept this offer?"
```

### 查看统计

```bash
vw stats
```

### 新增案例

```bash
vw add-case \
  --id case_001 \
  --domain career \
  --title "Accept offer or not" \
  --description "Two options with different growth paths" \
  --lesson-core "Clarify priority before choosing"
```

### 导入 CSV

```bash
vw import-csv --file ./cases.csv
```

### 导入文档

```bash
vw ingest-doc --file ./docs/a.pdf --type auto
vw ingest-doc --file ./docs/a.docx --type auto
```

## 常用 API

- `GET /stats`
- `GET /cases`
- `GET /cases/{case_id}`
- `POST /query`
- `GET /graph`
- `POST /decisions`
- `POST /ingest/json/async`
- `GET /tasks/{task_id}`
- `GET /ai/config`
- `POST /ai/config`

## 常用开发命令

### 后端

```bash
pytest
ruff check .
mypy src/
```

### 前端

```bash
cd frontend
pnpm lint
pnpm build
```

## 配置

主要配置文件:

- 默认配置: [config/default.yaml](d:/Administrator/Desktop/Full%20Stack/VintageWisdom/config/default.yaml)
- 用户配置: [config/user.yaml](d:/Administrator/Desktop/Full%20Stack/VintageWisdom/config/user.yaml)

常用环境变量:

```bash
VW_DATA_DIR=/path/to/data
VW_CONFIG_DIR=/path/to/config
VW_LOG_LEVEL=INFO
```

PowerShell:

```powershell
$env:VW_DATA_DIR = "D:\\path\\to\\data"
$env:VW_CONFIG_DIR = "D:\\path\\to\\config"
$env:VW_LOG_LEVEL = "INFO"
```

## 目录结构

```text
VintageWisdom/
├─ src/vintagewisdom/      Python 后端
├─ frontend/               Next.js 前端
├─ config/                 配置文件
├─ data/                   本地数据目录
├─ tests/                  测试
├─ docs/                   文档
└─ README.md
```

## 你现在最短的启动方法

如果你只是想马上跑起来，用这组命令就够了:

```bash
uv sync --extra dev --extra web --extra ingest
python -m vintagewisdom init
python -m uvicorn vintagewisdom.web.app:create_app --factory --host 127.0.0.1 --port 8000 --reload
```

新开一个终端:

```bash
cd frontend
pnpm install
pnpm dev
```

然后打开:

```text
http://127.0.0.1:3000
```

## 说明

- 当前主工作流是 Web API + 前端
- CLI 更适合初始化、批量导入和快速排查
- `pnpm lint` 目前还有一批图谱底层历史类型问题，主要集中在 Sigma 相关文件；`pnpm build` 和 `pnpm exec tsc --noEmit` 已可通过

## 相关文档

- [docs/README.md](d:/Administrator/Desktop/Full%20Stack/VintageWisdom/docs/README.md)
- [docs/design/UI-DESIGN.md](d:/Administrator/Desktop/Full%20Stack/VintageWisdom/docs/design/UI-DESIGN.md)
- [docs/architecture/ARCHITECTURE.md](d:/Administrator/Desktop/Full%20Stack/VintageWisdom/docs/architecture/ARCHITECTURE.md)
- [docs/architecture/STRUCTURE.md](d:/Administrator/Desktop/Full%20Stack/VintageWisdom/docs/architecture/STRUCTURE.md)
