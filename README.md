# VintageWisdom - 个人历史教训复用系统

> **让过去的智慧照亮未来的决策**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

---

## 简介

VintageWisdom 是一个**个人决策支持系统**，帮助你结构化存储历史决策案例，通过AI增强的检索与推演能力，在面临新决策时快速找到相关经验教训，避免重复犯错。

### 核心特点

- **完全本地化** - 所有数据存储在本地，保护隐私
- **AI增强** - 多标签领域分类、智能检索、因果推演（规划中）
- **跨领域迁移** - 发现技术/商业/政治等领域的深层相似性
- **持续进化** - 越用越聪明，形成个人决策理论

### 当前已实现（与代码同步）

- **Web API（FastAPI）** - 案例列表/查询/导入/图谱等接口
- **前端 Dashboard（Next.js + Sigma.js）** - 导入页、决策查询页、知识图谱交互
- **异步 JSON 导入** - 任务化导入 + 分阶段进度（import / classify / kg）
- **4 主域多标签分类** - HIS / FIN / CAR / TEC（支持二级 code），结果落库到 `domain_tags`
- **图谱强弱可视化** - 边强度统一为 `edge.strength`；KG 同对实体多关系聚合（策略 C：`1-∏(1-conf)`）

---

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/vintagewisdom.git
cd vintagewisdom

# 使用 uv 安装（推荐）
uv sync

# 或使用 pdm
pdm install

# 或使用 pip
pip install -e ".[dev]"
```

### 初始化

```bash
# 初始化本地数据存储（默认在 data/ 下创建 SQLite）
python -m vintagewisdom init
# 或（安装后）
vw init
```

### 运行

```bash
# 当前以 Web + 前端为主；CLI 可用于初始化/基础命令

# 使用命令行查询
vw query "我应该接受这个offer吗？"

# 添加新案例（示例）
vw add-case \
  --id case_001 \
  --domain career \
  --title "接受 offer 的权衡" \
  --description "两个选择：接受/拒绝" \
  --lesson-core "明确优先级与可逆性"

# 查看统计
vw stats
```

### 批量导入（CSV / PDF / Word）

```bash
# 从单个 CSV 导入
vw import-csv --file ./cases.csv

# 自动扫描目录并导入新 CSV（按文件 sha256 幂等去重）
vw scan-csv --dir ./imports --once
# 或持续扫描
vw scan-csv --dir ./imports --interval 5

# 抽取 PDF/DOCX 文本并入库（按文件 sha256 幂等去重）
# 需要安装可选依赖：
pip install -e ".[ingest]"

vw ingest-doc --file ./docs/a.pdf --type auto
vw ingest-doc --file ./docs/a.docx --type auto
```

### Web API（供前端调用）

安装并启动：

```bash
pip install -e ".[web]"
python -m uvicorn vintagewisdom.web.app:create_app --factory --host 127.0.0.1 --port 8000
```

常用接口：

- **GET `/stats`** 统计
- **GET `/cases`** 案例列表
- **POST `/query`** 决策查询（JSON：`{"text": "..."}`）
- **GET `/graph`** 知识图谱（返回 `nodes/edges`）
- **POST `/ingest/json/async`** 异步 JSON 导入（返回 task_id，轮询 `/tasks/{task_id}`）

### 前端（仪表盘 / 决策查询 / 知识图谱）

前端位于 `frontend/`，默认读取后端：

- `NEXT_PUBLIC_API_BASE`（未设置则默认 `http://127.0.0.1:8000`）

启动开发环境：

```bash
cd frontend
pnpm install
pnpm dev
```

访问：

- `http://localhost:3000/query` 决策查询
- `http://localhost:3000/graph` 知识图谱（节点/边可缩放拖拽，点击节点查看关联数据）

---

## 使用场景

### 场景1：决策前快速参考

```
你："我是一个A轮公司CTO，技术债很重，想重构但业务压力大"

系统：
┌──────────────────────────────────────────┐
│  【高度匹配案例】                          │
│  1. 某SaaS公司重构失败 (2021)              │
│     相似度: 92%  |  领域: tech+business    │
│     关键差异: 你处于A轮，案例为B轮          │
│                                          │
│  2. 某电商公司渐进式重构 (2019)             │
│     相似度: 85%  |  结果: 成功              │
│                                          │
│  【风险推演】                              │
│  若立即全面重构：                          │
│    3个月内：开发停滞，客户投诉上升            │
│    6个月内：核心员工流失，融资受阻            │
│    历史概率：基于3个相似案例，70%失败        │
│                                          │
│  【建议路径】                              │
│  方案A: 绞杀者策略（推荐）                   │
│    - 新功能用新架构，旧系统逐步替换           │
│    - 关键检查项:                            │
│      ☐ 是否划定"冻结区"，旧代码只修不增？    │
│      ☐ 新业务是否能在新架构上跑通MVP？       │
└──────────────────────────────────────────┘
```

### 场景2：记录决策形成闭环

```bash
# 记录当前决策
vw log-decision \
  --id dec_001 \
  --query "是否接受新工作 offer" \
  --context "薪资基本符合预期，但希望明确晋升路径" \
  --choice "先谈判再决定" \
  --predict "6个月内适应新环境"

# 过一段时间后回填结果
vw evaluate-decision \
  --id dec_001 \
  --outcome "基本符合预期，但晋升比想象慢"

# 查看统计（会显示已评估数量）
vw stats
```

### 场景3：发现个人决策模式

```bash
# 当前版本暂未提供自动报告生成命令。
# 你可以通过积累案例后使用 stats + query 辅助复盘。

# 输出：
┌─────────────────────────────────────────┐
│  你的决策理论 v1.0                       │
├─────────────────────────────────────────┤
│                                         │
│  【高胜率情境】                          │
│  • 信息完整度>80%                        │
│  • 时间压力<中等                         │
│  • 可逆性高                              │
│  胜率: 85%                               │
│                                         │
│  【危险信号组合】                         │
│  • 时间压力高 + 情绪标记激动 → 后悔率85%  │
│  • 涉及人际冲突 + 深夜时段 → 后悔率78%    │
│                                         │
│  【你的独特优势】                         │
│  • 技术架构决策胜率82%（高于平均70%）      │
│                                         │
│  【系统性弱点】                          │
│  • 涉及"拒绝他人"的决策胜率仅45%          │
│    原因：过度考虑关系维护                  │
└─────────────────────────────────────────┘
```

---

## 核心功能

### 1. 混合检索

结合向量相似度、约束条件过滤、知识图谱关联，三层召回精准匹配相关案例。

```python
# 示例：检索相关案例
results = engine.retrieve(
    query="技术债重构困境",
    constraints={"stage": "A轮", "role": "CTO"},
    top_k=5
)
```

### 2. 因果推演

自动挖掘案例中的因果链，识别关键路径和瓶颈节点。

```
技术债务积累 → 开发速度下降 → 团队士气低落 → 核心员工离职 → 项目延期
     │              │              │
     └──────────────┴──────────────┘
           最佳干预点：团队士气阶段
```

### 3. AI红队对抗

AI扮演反对者角色，系统性挑战你的决策假设。

- **事实基础攻击** - 质疑数据来源
- **逻辑结构攻击** - 检验推理链条
- **隐含假设攻击** - 暴露未明说的前提
- **极端情境攻击** - 测试最坏情况预案
- **机会成本攻击** - 探索替代选项

### 4. "未来你"对话

AI生成成功、失败、中立三个版本的"未来你"，帮助你从时间透视的角度审视当前决策。

```
成功未来你："接受这份工作是我职业生涯最好的决定之一，
             但关键是入职第3个月我主动调整了职责范围..."

失败未来你："我低估了'高压'的复合效应，
             第4个月开始失眠，第6个月失去阅读专注力..."
```

### 5. 偏见检测

实时检测认知偏见，防止决策偏差。

| 偏见类型 | 检测信号 | 干预方式 |
|---------|---------|---------|
| 确认偏误 | 只看支持证据 | 强制呈现反方案例 |
| 计划谬误 | 持续低估时间 | 注入历史基础率 |
| 沉没成本 | "已经投入了" | 清零视角重构 |
| 近因效应 | 忽视早期案例 | 时间权重调整 |

---

## 项目结构

```
vintagewisdom/
├── src/vintagewisdom/          # 后端源代码
│   ├── web/                   # FastAPI Web API
│   ├── core/                  # 核心流程（检索/异步导入）
│   ├── storage/               # SQLite/任务进度等
│   ├── knowledge/             # 领域体系/知识图谱（抽取/存储/聚合）
│   ├── ai/                    # 本地 Ollama 分类器等
│   ├── models/                # 数据模型
│   └── ...
├── frontend/                   # 前端（Next.js）
├── data/                       # 本地数据（SQLite db 等）
├── config/                     # 配置文件
├── tests/                      # 测试
└── docs/                       # 文档
```

详细结构见 [STRUCTURE.md](STRUCTURE.md)

---

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| **界面** | 终端 CLI（argparse） | 查询/录入/统计 |
| **存储** | SQLite（本地文件） | 案例持久化 |
| **配置** | YAML | 默认配置 + 用户覆盖 |
| **数据模型** | Pydantic v2 | 数据校验 |
| **语言** | Python 3.10+ | 主要开发语言 |

详细设计见 [DESIGN.md](DESIGN.md)

---

## 配置

### 基础配置

编辑 `config/user.yaml`：

```yaml
user:
  name: "你的名字"
  preferred_domain: ["tech", "business"]

preferences:
  compression_level: "standard"  # minimal/standard/deep/archaeology
  redteam_intensity: "medium"    # low/medium/high
  language: "zh"

privacy:
  local_only: true
```

### 环境变量

```bash
export VW_DATA_DIR="/path/to/data"
export VW_CONFIG_DIR="/path/to/config"
export VW_LOG_LEVEL="INFO"
```

Windows（PowerShell）示例：

```powershell
$env:VW_DATA_DIR = "D:\\path\\to\\data"
$env:VW_CONFIG_DIR = "D:\\path\\to\\config"
$env:VW_LOG_LEVEL = "INFO"
```

---

## 开发

### 设置开发环境

```bash
# 安装开发依赖
uv sync --extra dev

# 安装 pre-commit
pre-commit install

# 运行测试
pytest

# 代码检查
ruff check .
mypy src/
```

### 项目演进路线

1. **习惯养成（0-3月）** - 建立决策记录习惯
2. **模式积累（3-12月）** - 发现个人决策模式
3. **深度校准（1-2年）** - 系统成为你的"外部自我"
4. **共生进化（2年+）** - 形成独特决策方法论

---

## 数据隐私

- **本地优先** - 所有案例数据存储在本地SQLite
- **可选联网** - 复杂推理可选择性使用云端API
- **加密备份** - 支持加密备份到私有云
- **数据导出** - 随时导出所有数据

---

## 贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与。

### 贡献方式

- 🐛 提交 Bug 报告
- 💡 提出新功能建议
- 📝 改进文档
- 🔧 提交代码修复
- 🧪 添加测试用例

---

## 许可证

[MIT License](LICENSE)

---

## 致谢

- 设计灵感来自《思考，快与慢》《创新者的窘境》
- 因果推理参考 Judea Pearl 的因果推断理论
- 偏见检测基于 Daniel Kahneman 的认知偏差研究

---

## 相关链接

- [设计文档](DESIGN.md)
- [项目结构](STRUCTURE.md)
- [用户指南](docs/user-guide/)
- [API文档](docs/api/)

---

<p align="center">
  <i>"历史不会重复，但会押韵" —— 马克·吐温</i>
</p>
