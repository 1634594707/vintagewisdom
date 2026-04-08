# VintageWisdom 下一阶段更新路线图（AI 驱动版本 + 批量导入/爬虫）

> 目标：在不破坏现有 CLI/Web API 的前提下，把增强能力升级为 **AI 驱动**（可本地/可云端、可降级），并把数据获取与导入升级为 **可扩展的数据管道**（批量文件 + 爬虫 + 表格处理）。

本文参考当前设计规范与演进路线（本地优先、可解释性、人机协作边界），并对齐当前已落地的 **插件化骨架**：

- `VintageWisdomApp` 统一生命周期与配置
- `EventBus`：`case.added`、`db.case.inserted`、`ingest.*`、`decision.before/decision.after`
- 插件默认全启用，配置 `plugins.disabled` 作为黑名单

---

## 0. 当前状态快照（你现在已经具备的能力）

- **导入**：Web 支持 CSV/JSON/Markdown/Document 导入，并发 `ingest.started/completed/failed`
- **分类**：严格多标签分类器（HIS/FIN/CAR/TEC 二级 code），已能落库
- **KG**：已具备 KG 抽取插件 `kg.extract`（AI 可用时后台抽取 + 幂等）
- **增强插件（MVP）**：
  - `ai.redteam`（模板质疑）
  - `bias.detector`（启发式偏见提示）
  - `ai.reasoning`（规则因果链抽取）
- **挂载点**：`Engine.query()` 已支持 `decision.before/decision.after`（插件可读写 reasoning/recommendations）

接下来主要升级两条线：

1) **AI 驱动的决策增强链**（从“模板/规则”升级为“LLM+证据+多步推理”）
2) **数据获取与导入管道**（批量文件 + 爬虫 + pandas/duckdb 处理）

---

## 1. AI 驱动版本：从“模板增强”到“证据约束的多步推理”

### 1.1 核心原则（与当前设计规范对齐）

- **本地优先，可选联网**：默认走本地 LLM（Ollama/LM Studio），失败再降级到规则/模板。
- **可解释性优先**：任何 AI 输出必须带 evidence 引用（来自 case、KG、导入文本片段），并可追溯。
- **人机协作边界**：AI 负责生成“问题/假设/反例/清单”，你负责确认事实与取舍。

### 1.2 统一一个“LLM 服务层”（强烈建议先做）

新增一个内核能力：`core/llm.py`（或做成插件 `ai.llm`），对外只暴露：

- `generate(prompt, *, model, temperature, json_schema=None, timeout_s=...)`
- `chat(messages, *, model, ...)`

并提供 **策略**：

- 本地优先：ollama
- 可选云端：OpenAI/兼容 API（通过 `api_base/api_key`）
- 失败回退：返回空，调用方必须可降级

配置建议：

```yaml
ai:
  provider: ollama  # ollama | api
  model: deepseek-r1:7b
  api_base: ""
  api_key: ""
  timeout_s: 30
  retries: 1
```

### 1.3 Evidence 聚合：把“案例证据”变成第一等公民

为 `decision.after` 增加一个约定字段（不破坏兼容）：

- `event.data["evidence"] = {"cases": [...], "snippets": [...], "kg_paths": [...]} `

落地方式（插件化）：

- 新插件：`evidence.builder`
  - 输入：`text`, `cases`
  - 输出：
    - case 摘要（id/title/lesson_core/outcome_result）
    - 关键片段（从 description/lesson_core 中截取）
    - KG 相关路径（如果 kg 可用）：case -> factor -> outcome

这样 redteam / reasoning / bias 的 AI 版本都能吃同一份 evidence。

### 1.4 AI 红队（ai.redteam）升级方案

目标：把“分层攻击”的思路落到代码，并且 **每一层都引用 evidence**。

实现策略（插件 `ai.redteam.llm`）：

- 监听：`decision.after`
- 输入：`query + topK cases + evidence`
- 输出：结构化 JSON（推荐）

示例 schema：

```json
{
  "layers": [
    {"type": "facts", "questions": ["..."], "evidence_refs": ["case:case_001"]},
    {"type": "logic", "attacks": ["..."], "evidence_refs": [...]},
    {"type": "assumptions", "assumptions": ["..."], "evidence_refs": [...]},
    {"type": "worst_case", "scenario": "...", "mitigation": ["..."]},
    {"type": "opportunity_cost", "alternatives": ["..."]},
    {"type": "reversibility", "steps": ["..."]}
  ]
}
```

渲染方式：把 redteam 输出追加到 reasoning；并把关键问题以 checklist 形式追加到 recommendations。

降级：
- LLM 不可用 → 继续使用当前模板版 `ai.redteam`（你已经实现）

### 1.5 偏见检测（bias.detector）升级方案

从“关键词提示”升级为“两段式”：

1) 规则快速筛（便宜）
2) LLM 验证与重写提示（更准）

插件 `bias.detector.llm`：
- 监听 `decision.before`：给出 `bias_hypotheses`
- 监听 `decision.after`：结合 evidence 输出 **干预建议**（怎么补信息/怎么反证）

### 1.6 因果推演（ai.reasoning）升级方案

目标：从规则抽取 → “规则 + LLM 补全 + KG 路径搜索”。

插件建议拆成三段（都监听 `decision.after`，按依赖顺序）：

- `reasoning.causal_extract`：规则抽取因果边（你已做 MVP）
- `reasoning.llm_refine`：LLM 对因果边做去噪、补充中间节点、给置信度
- `reasoning.kg_paths`：如果 KG 可用，在图中找路径，作为 evidence

最终把“因果链 + 关键干预点 + 风险信号”写入 reasoning。

---

## 2. 批量导入 + 爬虫：统一成“数据管道”

你提的想法非常正确：接下来系统价值增长主要来自 **数据规模与质量**。建议把输入统一成一套可扩展 pipeline。

### 2.1 统一 ingestion 概念：Source -> Record -> Case

新增抽象（可以先在 `core/ingest/` 下实现，后续再拆插件）：

- **Source**：文件、URL、RSS、网页、API
- **Record**：原始条目（DataFrame 行 / JSON item / HTML 文档）
- **CaseCandidate**：候选 case（含原文、元数据、来源信息）
- **Case**：最终入库结构化对象

关键点：保留原文与来源（可审计）。

### 2.2 批量文件导入（文件夹 + 多格式）

建议新增 CLI：

- `vw ingest-dir --dir ./imports --pattern "**/*" --workers 4`

流程：
- 遍历目录
- 对每个文件计算 sha256（你已有幂等机制）
- 按后缀路由：csv/json/md/pdf/docx/html
- 发 `ingest.*` 事件（开始/完成/失败），并写 `file_ingests` 表

### 2.3 爬虫（采集层）

按当前规划推荐：`crawl4ai + playwright`。

建议作为插件 `ingest.crawler`：

- 提供 CLI：`vw crawl --seed urls.txt --out data/crawl/`
- 输出标准化：每条页面保存为 `jsonl`：

```json
{"url": "...", "fetched_at": "...", "title": "...", "text": "...", "html_path": "...", "meta": {...}}
```

然后把 crawl 输出喂给同一条“normalize->case” pipeline。

### 2.4 表格处理：pandas vs 更好的选择

- **pandas**：适合 10万行以内、快速开发、生态强。
- **duckdb**：更适合大规模（百万行）、SQL 清洗、低内存。

建议：
- 默认用 pandas（简单）
- 当数据量大/需要复杂 join/聚合 → 可选 duckdb

落地方式：

- 插件 `ingest.tabular`：
  - `normalize_dataframe(df) -> df`（列名规范、空值、日期、去重）
  - `map_to_case_candidates(df) -> List[CaseCandidate]`

### 2.5 质量控制：去重、冲突策略、人工校验

必须补齐的机制：

- 去重：
  - source sha256（文件级）
  - content sha1（文本级）
- 冲突策略：skip/replace/merge
- 人工校验队列（后期）：把低置信度/冲突记录放入 review 表

---

## 3. 路线图（按优先级/里程碑）

### M1（1-2 周）：AI 服务层 + Evidence Builder

- [ ] `core/llm`：统一本地/云端 LLM 调用 + 超时/回退
- [ ] `evidence.builder` 插件：为 `decision.after` 构建 evidence
- [ ] `ai.redteam.llm` 插件：实现分层攻击 JSON 输出 + 渲染
- [ ] 回归：无 LLM 时不崩，继续用模板版

### M2（2-4 周）：导入管道 v1（批量文件 + 标准化）

- [ ] `vw ingest-dir`：批量导入目录（多格式路由）
- [ ] `ingest.tabular`：pandas 规范化与字段映射
- [ ] 任务化：沿用现有 async ingest 任务模型（或扩展）

### M3（4-8 周）：爬虫 + 大规模数据清洗

- [ ] `vw crawl`：crawl4ai/playwright 拉取网页，落 jsonl
- [ ] `duckdb` 可选接入：大规模清洗/聚合
- [ ] “来源与许可”治理：robots/站点条款、限速、缓存

### M4（8-12 周）：偏见与因果推演 AI 化

- [ ] `bias.detector.llm`：规则筛 + LLM 验证 + 干预建议
- [ ] `reasoning.llm_refine`：因果链补全与置信度
- [ ] `reasoning.kg_paths`：图谱路径证据化

---

## 4. 配置与开关（强烈建议标准化）

建议在 `config/default.yaml` 增加：

```yaml
plugins:
  disabled: []
  config:
    ai.redteam:
      mode: "llm"   # llm | template
    bias.detector:
      mode: "llm"   # llm | heuristic
    ai.reasoning:
      mode: "llm"   # llm | rule

ai:
  provider: "ollama"
  model: "deepseek-r1:7b"
  timeout_s: 30
```

并保证：任何插件在外部依赖不可用时 **自动降级**。

---

## 5. 风险与约束（必须提前处理）

- **LLM 幻觉风险**：必须 evidence 引用 + “不确定就提示你补信息”。
- **性能**：LLM 调用走后台/缓存；`decision.after` 可做“快速版/深度版”两档。
- **爬虫合规**：robots、限速、缓存、来源记录。
- **数据污染**：导入阶段要严格 schema 校验与去重。

---

## 6. 你下一步该怎么做（建议）

如果你想最快看到 AI 驱动的质变：

1) 先做 **M1：LLM 服务层 + Evidence Builder + Redteam LLM**
2) 然后做 **M2：批量导入目录**（先把你现有资料灌进来）
3) 再做 **爬虫**（把公开案例变成你的“外部案例库”）

当案例数量上来后（>50），bias 与 reasoning 的 AI 化收益会显著上升。
