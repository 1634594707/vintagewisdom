# VintageWisdom - 项目结构文档

## 目录结构

```
vintagewisdom/
├── README.md                 # 项目说明文档
├── docs/design/UI-DESIGN.md  # 系统设计文档
├── docs/architecture/STRUCTURE.md  # 本文档
├── LICENSE                   # 开源许可证
│
├── pyproject.toml            # Python项目配置
├── uv.lock / pdm.lock        # 依赖锁定文件
├── .python-version           # Python版本指定
│
├── .env.example              # 环境变量示例
├── .gitignore                # Git忽略规则
├── .dockerignore             # Docker忽略规则
│
├── docker/
│   ├── Dockerfile            # Docker构建文件
│   └── docker-compose.yml    # Docker Compose配置
│
├── docs/                     # 文档目录
│   ├── api/                  # API文档
│   ├── user-guide/           # 用户指南
│   └── development/          # 开发文档
│
├── src/                      # 源代码目录
│   └── vintagewisdom/        # 主包
│       ├── __init__.py
│       ├── __main__.py       # 入口点
│       │
│       ├── cli/              # 命令行界面
│       │   ├── __init__.py
│       │   ├── app.py        # TUI主应用
│       │   ├── commands.py   # 命令定义
│       │   └── widgets.py    # 自定义组件
│       │
│       ├── core/             # 核心引擎
│       │   ├── __init__.py
│       │   ├── engine.py     # 主引擎协调器
│       │   ├── retriever.py  # 混合检索引擎
│       │   ├── reasoner.py   # 因果推理引擎
│       │   └── recommender.py # 干预推荐器
│       │
│       ├── models/           # 数据模型
│       │   ├── __init__.py
│       │   ├── case.py       # 案例模型
│       │   ├── entity.py     # 实体模型
│       │   ├── pattern.py    # 模式模型
│       │   └── decision.py   # 决策模型
│       │
│       ├── storage/          # 数据存储
│       │   ├── __init__.py
│       │   ├── database.py   # SQLite管理
│       │   ├── vector_store.py # FAISS向量存储
│       │   ├── graph_store.py  # NetworkX图谱
│       │   └── backup.py     # 备份管理
│       │
│       ├── nlp/              # 自然语言处理
│       │   ├── __init__.py
│       │   ├── embedder.py   # 文本嵌入
│       │   ├── extractor.py  # 实体/关系提取
│       │   ├── classifier.py # 意图分类
│       │   └── causal.py     # 因果抽取
│       │
│       ├── ai/               # AI增强模块
│       │   ├── __init__.py
│       │   ├── redteam.py    # 红队对抗
│       │   ├── future_self.py # 未来你对话
│       │   ├── pressure_test.py # 压力测试
│       │   └── adapter.py    # 模型适配器
│       │
│       ├── knowledge/        # 知识管理
│       │   ├── __init__.py
│       │   ├── patterns.py   # 模式库管理
│       │   ├── mappings.py   # 跨领域映射
│       │   └── lessons.py    # 教训提取
│       │
│       ├── bias/             # 偏见检测
│       │   ├── __init__.py
│       │   ├── detector.py   # 偏见检测器
│       │   ├── feedback.py   # 反馈机制
│       │   └── calibration.py # 校准曲线
│       │
│       ├── visualization/    # 可视化
│       │   ├── __init__.py
│       │   ├── graph_viz.py  # 图谱可视化
│       │   ├── causal_viz.py # 因果链可视化
│       │   └── report.py     # 报告生成
│       │
│       ├── utils/            # 工具函数
│       │   ├── __init__.py
│       │   ├── config.py     # 配置管理
│       │   ├── logger.py     # 日志管理
│       │   ├── validators.py # 数据验证
│       │   └── helpers.py    # 辅助函数
│       │
│       └── web/              # Web界面（可选）
│           ├── __init__.py
│           ├── app.py        # Gradio/FastAPI应用
│           └── components.py # 页面组件
│
├── data/                     # 数据目录（用户数据）
│   ├── cases/                # 案例存储
│   │   ├── business/         # 商业领域
│   │   ├── tech/             # 技术领域
│   │   └── political/        # 政治领域
│   │
│   ├── vectors/              # 向量索引
│   │   ├── case_vectors.index
│   │   └── entity_vectors.index
│   │
│   ├── graph/                # 图谱数据
│   │   ├── graph.db
│   │   └── layouts/
│   │
│   ├── patterns/             # 模式库
│   │   ├── se_patterns.yaml  # 软件工程模式
│   │   ├── biz_patterns.yaml # 商业模式
│   │   └── cross_mappings.yaml # 跨领域映射
│   │
│   ├── exports/              # 导出文件
│   │   ├── reports/          # 报告
│   │   └── snapshots/        # 快照
│   │
│   └── backups/              # 自动备份
│
├── models/                   # 本地模型（下载/训练）
│   ├── embeddings/           # 嵌入模型
│   ├── llm/                  # 本地LLM
│   └── spacy/                # spaCy模型
│
├── config/                   # 配置文件
│   ├── default.yaml          # 默认配置
│   ├── user.yaml             # 用户配置（gitignore）
│   └── prompts/              # 提示词模板
│       ├── redteam.txt
│       ├── future_self.txt
│       └── analysis.txt
│
├── tests/                    # 测试目录
│   ├── __init__.py
│   ├── conftest.py           # pytest配置
│   ├── unit/                 # 单元测试
│   │   ├── test_models.py
│   │   ├── test_retriever.py
│   │   └── test_bias.py
│   ├── integration/          # 集成测试
│   │   ├── test_workflow.py
│   │   └── test_api.py
│   └── fixtures/             # 测试数据
│       └── sample_cases.json
│
├── scripts/                  # 脚本工具
│   ├── setup.sh              # 初始化脚本
│   ├── backup.sh             # 备份脚本
│   ├── migrate.py            # 数据迁移
│   └── benchmark.py          # 性能测试
│
└── examples/                 # 示例
    ├── import_cases.py       # 导入案例示例
    ├── analyze_decision.py   # 分析决策示例
    └── custom_pattern.py     # 自定义模式示例
```

---

## 模块详细说明

### 1. CLI模块 (`src/vintagewisdom/cli/`)

命令行界面，基于Textual构建的TUI应用。

**核心组件：**
- `app.py`: 主应用入口，管理界面路由
- `commands.py`: 命令定义（查询、录入、分析等）
- `widgets.py`: 自定义UI组件（案例卡片、因果图等）

**功能：**
- 案例录入表单
- 决策查询界面
- 因果图谱可视化
- 设置管理

### 2. Core模块 (`src/vintagewisdom/core/`)

系统核心引擎，协调各子系统工作。

**核心组件：**
- `engine.py`: 主引擎，协调检索-推理-推荐流程
- `retriever.py`: 混合检索（向量+约束+图谱）
- `reasoner.py`: 因果推理与路径发现
- `recommender.py`: 干预策略推荐

**工作流程：**
```
用户输入 → 意图解析 → 混合检索 → 因果推演 → 生成报告
```

### 3. Models模块 (`src/vintagewisdom/models/`)

数据模型定义，使用Pydantic进行验证。

**核心模型：**
- `Case`: 案例模型（决策情境、行动、结果）
- `Entity`: 实体模型（人物、组织、因素）
- `Pattern`: 模式模型（因果模式、约束条件）
- `Decision`: 决策模型（当前决策记录）

### 4. Storage模块 (`src/vintagewisdom/storage/`)

数据持久化层，管理所有数据存储。

**核心组件：**
- `database.py`: SQLite数据库管理
- `vector_store.py`: FAISS向量索引
- `graph_store.py`: NetworkX图谱存储
- `backup.py`: 自动备份与恢复

**存储策略：**
```
热数据：Redis + 本地SSD（最近1年）
温数据：本地SSD + 网络存储（1-3年）
冷数据：对象存储（3年+）
```

### 5. NLP模块 (`src/vintagewisdom/nlp/`)

自然语言处理，文本理解与抽取。

**核心组件：**
- `embedder.py`: Sentence-BERT文本嵌入
- `extractor.py`: spaCy实体与关系提取
- `classifier.py`: 意图与领域分类
- `causal.py`: 因果触发词识别与抽取

### 6. AI模块 (`src/vintagewisdom/ai/`)

AI增强功能，高级推理与对话。

**核心组件：**
- `redteam.py`: 红队对抗机制
- `future_self.py`: "未来你"对话生成
- `pressure_test.py`: 决策压力测试
- `adapter.py`: 本地/云端模型适配

### 7. Knowledge模块 (`src/vintagewisdom/knowledge/`)

知识管理，模式库与跨领域映射。

**核心组件：**
- `patterns.py`: 模式库管理（CRUD+验证）
- `mappings.py`: 跨领域映射规则
- `lessons.py`: 教训提取与适配

### 8. Bias模块 (`src/vintagewisdom/bias/`)

认知偏见检测与校准。

**核心组件：**
- `detector.py`: 偏见检测（确认偏误、计划谬误等）
- `feedback.py`: 实时反馈机制
- `calibration.py`: 预测校准曲线

### 9. Visualization模块 (`src/vintagewisdom/visualization/`)

可视化输出，图表与报告生成。

**核心组件：**
- `graph_viz.py`: 知识图谱可视化（Pyvis）
- `causal_viz.py`: 因果链可视化
- `report.py`: Markdown/PDF报告生成

---

## 数据流

### 案例录入流程

```
用户输入（自然语言）
    ↓
NLP处理（实体提取、向量化）
    ↓
结构化存储（SQLite + FAISS + JSONL）
    ↓
图谱更新（NetworkX添加节点/边）
    ↓
模式检测（是否触发新模式）
    ↓
用户确认（验证提取结果）
```

### 决策查询流程

```
用户查询（自然语言）
    ↓
意图解析（领域识别、实体提取）
    ↓
混合检索（向量+约束+图谱）
    ↓
融合排序（多维度评分）
    ↓
因果推演（路径发现、风险预测）
    ↓
AI增强（红队对抗、压力测试）
    ↓
生成报告（案例+检查清单+建议）
```

### 反馈闭环流程

```
决策执行（现实世界）
    ↓
结果记录（用户输入或自动抓取）
    ↓
偏差计算（预测vs实际）
    ↓
模式校准（更新因果置信度）
    ↓
个人模型更新（偏见检测参数）
    ↓
知识库进化（模式提取与验证）
```

---

## 配置文件

### 默认配置 (`config/default.yaml`)

```yaml
app:
  name: "VintageWisdom"
  version: "0.1.0"
  debug: false

storage:
  database_path: "data/vintagewisdom.db"
  vector_index_path: "data/vectors"
  graph_path: "data/graph"
  backup_enabled: true
  backup_interval: "daily"

nlp:
  embedding_model: "paraphrase-multilingual-MiniLM-L12-v2"
  spacy_model_zh: "zh_core_web_sm"
  spacy_model_en: "en_core_web_sm"
  max_sequence_length: 512

retrieval:
  vector_weight: 0.4
  constraint_weight: 0.3
  graph_weight: 0.3
  top_k: 5

ai:
  local_model: "phi-3-mini"
  use_cloud: false
  cloud_model: "gpt-4"
  redteam_enabled: true
  future_self_enabled: true

bias_detection:
  confirmation_bias_threshold: 0.7
  planning_fallacy_threshold: 1.5
  emotion_check_enabled: true
```

### 用户配置 (`config/user.yaml`)

用户自定义配置，覆盖默认值。

```yaml
user:
  name: ""
  preferred_domain: ["tech", "business"]
  
preferences:
  compression_level: "standard"  # minimal/standard/deep/archaeology
  redteam_intensity: "medium"    # low/medium/high
  language: "zh"
  
privacy:
  local_only: true
  allow_cloud_for: ["complex_reasoning"]
  
custom_patterns:
  - name: "我的技术债务模式"
    triggers: ["重构", "技术债"]
```

---

## 数据库Schema

### 案例表 (cases)

```sql
CREATE TABLE cases (
    id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    decision_node TEXT,
    action_taken TEXT,
    outcome_result TEXT,
    outcome_timeline TEXT,
    lesson_core TEXT,
    confidence TEXT CHECK(confidence IN ('low', 'medium', 'high')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 实体表 (entities)

```sql
CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- person, organization, factor, era
    attributes JSON,
    embedding BLOB
);
```

### 关系表 (relations)

```sql
CREATE TABLE relations (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    attributes JSON,
    weight REAL DEFAULT 1.0,
    FOREIGN KEY (source_id) REFERENCES entities(id),
    FOREIGN KEY (target_id) REFERENCES entities(id)
);
```

### 模式表 (patterns)

```sql
CREATE TABLE patterns (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    domain TEXT NOT NULL,
    trigger_conditions JSON,
    causal_chain JSON,
    intervention_points JSON,
    confidence_score REAL,
    case_count INTEGER,
    verified BOOLEAN DEFAULT FALSE
);
```

### 决策日志表 (decision_logs)

```sql
CREATE TABLE decision_logs (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    context JSON,
    recommended_cases JSON,
    user_decision TEXT,
    predicted_outcome TEXT,
    actual_outcome TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    evaluated_at TIMESTAMP
);
```

---

## 开发规范

### 代码风格

- 使用 `ruff` 进行代码格式化
- 使用 `mypy` 进行类型检查
- 遵循 PEP 8 规范
- 最大行长度：100字符

### 测试规范

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 覆盖率报告
pytest --cov=vintagewisdom --cov-report=html
```

### 提交规范

```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

---

## 部署方式

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/yourusername/vintagewisdom.git
cd vintagewisdom

# 安装依赖
uv sync
# 或
pdm install

# 初始化数据目录
python -m vintagewisdom init

# 运行TUI
python -m vintagewisdom
```

### Docker部署

```bash
# 构建镜像
docker build -t vintagewisdom .

# 运行容器
docker run -v $(pwd)/data:/app/data vintagewisdom

# Docker Compose
docker-compose up -d
```

### 生产部署

```bash
# 使用systemd服务
sudo cp scripts/vintagewisdom.service /etc/systemd/system/
sudo systemctl enable vintagewisdom
sudo systemctl start vintagewisdom
```

---

*文档版本: 1.0*  
*最后更新: 2026-03-15*
