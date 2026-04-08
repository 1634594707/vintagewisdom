# VintageWisdom API 接口规范文档

## 概述

VintageWisdom 后端基于 FastAPI 构建，提供 RESTful API 接口，支持案例管理、决策查询、知识图谱、文件导入等核心功能。

**基础信息：**
- 默认地址：`http://127.0.0.1:8000`
- API 文档：`http://127.0.0.1:8000/docs`
- 所有接口支持 CORS 跨域访问

---

## 1. 系统基础接口

### 1.1 健康检查
```
GET /health
```

**响应示例：**
```json
{
  "status": "ok"
}
```

### 1.2 系统统计
```
GET /stats
```

**响应示例：**
```json
{
  "cases": 128,
  "decision_logs": 42,
  "evaluated_decision_logs": 27
}
```

### 1.3 调试信息
```
GET /debug/db
```

**响应示例：**
```json
{
  "db_path": "/path/to/vintagewisdom.db",
  "cases": 128,
  "decision_logs": 42,
  "entities": 256,
  "relations": 512
}
```

---

## 2. 案例管理接口

### 2.1 获取案例列表
```
GET /cases
```

**响应示例：**
```json
[
  {
    "id": "TEC-REF-001",
    "domain": "TEC-REF",
    "title": "SaaS platform refactor under delivery pressure",
    "description": "...",
    "decision_node": "...",
    "action_taken": "...",
    "outcome_result": "...",
    "outcome_timeline": "6 to 12 months",
    "lesson_core": "...",
    "confidence": "high",
    "tags": ["refactor", "technical-debt"],
    "created_at": "2025-12-14T00:00:00Z",
    "updated_at": "2026-03-29T00:00:00Z"
  }
]
```

### 2.2 获取单个案例
```
GET /cases/{case_id}
```

**路径参数：**
- `case_id`: 案例ID

**响应：** 同案例对象结构

### 2.3 获取相似案例
```
GET /cases/{case_id}/similar?threshold=0.3
```

**路径参数：**
- `case_id`: 案例ID

**查询参数：**
- `threshold`: 相似度阈值（0-1），默认 0.3

**响应示例：**
```json
{
  "case_id": "TEC-REF-001",
  "similar_cases": [
    {
      "case_id": "TEC-REF-002",
      "similarity": 0.85,
      "reasons": ["相同领域", "相似决策节点", "类似结果"]
    }
  ]
}
```

---

## 3. 决策查询接口

### 3.1 决策查询
```
POST /query
```

**请求体：**
```json
{
  "text": "平台团队技术债不断上升，但交付压力依旧很高，现在应该整体重构还是分阶段迁移？",
  "mode": "default"
}
```

**响应示例：**
```json
{
  "matches": 5,
  "cases": [
    {
      "id": "TEC-REF-001",
      "domain": "TEC-REF",
      "title": "...",
      "description": "...",
      "lesson_core": "..."
    }
  ],
  "reasoning": "基于历史案例分析，当技术债和交付压力同时存在时...",
  "recommendations": [
    "建议采用分阶段迁移策略",
    "优先处理高风险模块",
    "建立技术债务清单"
  ]
}
```

---

## 4. AI 自动分类接口

### 4.1 文本自动分类
```
POST /classify
```

**请求体：**
```json
{
  "text": "这是一个关于技术重构的案例..."
}
```

**响应示例：**
```json
{
  "suggestions": [
    {
      "domain": "TEC-REF",
      "confidence": 0.85,
      "reason": "文本包含技术重构相关关键词"
    },
    {
      "domain": "TEC-DEBT",
      "confidence": 0.72,
      "reason": "提到技术债务管理"
    }
  ]
}
```

---

## 5. 知识图谱接口

### 5.1 获取图谱数据
```
GET /graph?view=case&use_ai_clustering=false&similarity_threshold=0.4
```

**查询参数：**
- `view`: 视图类型，`case`（案例图谱）或 `kg`（知识图谱）
- `q`: 搜索关键词（可选）
- `seed_entity_id`: 种子实体ID（可选）
- `relation_type`: 关系类型过滤（可选）
- `depth`: 展开深度，1-3，默认 2
- `max_entities`: 最大实体数，默认 300
- `max_relations`: 最大关系数，默认 600
- `use_ai_clustering`: 是否启用 AI 聚类，默认 false
- `similarity_threshold`: 相似度阈值，默认 0.4
- `max_cases_for_similarity`: 用于相似度计算的最大案例数，默认 200
- `max_similar_edges`: 最大相似边数，默认 60

**响应示例（案例视图）：**
```json
{
  "nodes": [
    {
      "id": "domain:TEC-REF",
      "type": "domain",
      "label": "TEC-REF",
      "domain": "TEC-REF"
    },
    {
      "id": "case:TEC-REF-001",
      "type": "case",
      "label": "SaaS platform refactor",
      "case_id": "TEC-REF-001",
      "domain": "TEC-REF"
    },
    {
      "id": "cluster:cluster_001",
      "type": "cluster",
      "label": "技术重构聚类",
      "cluster_theme": "技术债务与重构决策"
    }
  ],
  "edges": [
    {
      "id": "e:domain:TEC-REF->case:TEC-REF-001",
      "source": "domain:TEC-REF",
      "target": "case:TEC-REF-001",
      "type": "has_case",
      "edge_type": "domain_case"
    },
    {
      "id": "similar:TEC-REF-001:TEC-REF-002",
      "source": "case:TEC-REF-001",
      "target": "case:TEC-REF-002",
      "type": "similar",
      "edge_type": "case_similar",
      "similarity": 0.85,
      "strength": 0.85,
      "reasons": ["相同领域", "相似决策节点"]
    }
  ],
  "clusters": [
    {
      "cluster_id": "cluster_001",
      "cluster_name": "技术重构聚类",
      "cases": ["TEC-REF-001", "TEC-REF-002"],
      "theme": "技术债务与重构决策"
    }
  ],
  "stats": {
    "domain_count": 5,
    "case_count": 128,
    "similar_edge_count": 45,
    "cluster_count": 8,
    "similarity_cases_used": 128
  }
}
```

### 5.2 获取节点详情
```
GET /kg/node/{entity_id}
```

**路径参数：**
- `entity_id`: 实体ID

**响应示例：**
```json
{
  "id": "entity_001",
  "type": "RiskType",
  "label": "技术债务风险",
  "attributes": {
    "description": "...",
    "severity": "high"
  }
}
```

### 5.3 获取热门实体
```
GET /kg/hot?limit=50
```

**查询参数：**
- `limit`: 返回数量限制，默认 50

**响应示例：**
```json
{
  "risk_types": [
    {
      "id": "risk_001",
      "name": "技术债务",
      "count": 45
    }
  ],
  "events": [
    {
      "id": "event_001",
      "name": "系统重构",
      "count": 32
    }
  ]
}
```

### 5.4 实体查找
```
GET /kg/lookup?kind=RiskType&name=技术债务
```

**查询参数：**
- `kind`: 实体类型
- `name`: 实体名称

**响应示例：**
```json
{
  "id": "risk_001",
  "kind": "RiskType",
  "name": "技术债务"
}
```

### 5.5 重建知识图谱
```
POST /kg/rebuild
```

**请求体：**
```json
{
  "limit_cases": 50,
  "force": false
}
```

**响应示例：**
```json
{
  "status": "ok",
  "cases_processed": 50,
  "entities_upserted": 150,
  "relations_upserted": 300,
  "evidence_upserted": 450
}
```

---

## 6. 文件导入接口

### 6.1 CSV 导入
```
POST /ingest/csv
```

**请求：** multipart/form-data
- `file`: CSV 文件
- `default_domain`: 默认领域（可选）
- `on_conflict`: 冲突策略，`skip` 或 `replace`，默认 `skip`
- `auto_classify`: 是否启用自动分类，`true` 或 `false`，默认 `false`
- `domains`: JSON 数组，选中的领域列表（可选）
- `tags`: JSON 数组，标签列表（可选）

**响应示例：**
```json
{
  "status": "success",
  "sha256": "abc123...",
  "imported": 45,
  "skipped": 3,
  "failed": 2,
  "case_ids": ["case_001", "case_002"],
  "auto_classified": true,
  "suggested_domains": ["TEC-REF", "CAR-NEG"]
}
```

### 6.2 JSON 同步导入
```
POST /ingest/json
```

**请求：** multipart/form-data
- `file`: JSON 文件
- `default_domain`: 默认领域（可选）
- `on_conflict`: 冲突策略
- `auto_classify`: 是否启用自动分类
- `domains`: 选中的领域列表（可选）
- `tags`: 标签列表（可选）

**响应：** 同 CSV 导入

### 6.3 JSON 异步导入（推荐）
```
POST /ingest/json/async
```

**请求：** multipart/form-data
- `file`: JSON 文件
- `default_domain`: 默认领域（可选）
- `auto_classify`: 是否启用 AI 自动分类
- `auto_cluster`: 是否启用 AI 自动聚类
- `domains`: 选中的领域列表（可选）
- `tags`: 标签列表（可选）

**响应示例：**
```json
{
  "status": "started",
  "task_id": "import_abc123",
  "total_cases": 100,
  "message": "导入任务已启动，请使用 /tasks/{task_id} 查询进度"
}
```

### 6.4 文档导入（PDF/DOCX）
```
POST /ingest/document
```

**请求：** multipart/form-data
- `file`: PDF 或 DOCX 文件
- `doc_type`: 文档类型，`auto`、`pdf` 或 `docx`，默认 `auto`
- `case_id`: 案例ID（可选，留空自动生成）
- `domain`: 领域代码（可选）
- `title`: 标题（可选，留空使用文件名）
- `auto_classify`: 是否启用自动分类
- `domains`: 选中的领域列表（可选）
- `tags`: 标签列表（可选）

**响应示例：**
```json
{
  "status": "success",
  "sha256": "def456...",
  "case_id": "case_doc_001",
  "auto_classified": true,
  "suggested_domains": ["TEC-AI", "TEC-ML"]
}
```

### 6.5 Markdown 导入
```
POST /ingest/markdown
```

**请求：** multipart/form-data
- `file`: Markdown 文件
- `case_id`: 案例ID（可选）
- `domain`: 领域代码（可选）
- `title`: 标题（可选）
- `auto_classify`: 是否启用自动分类
- `domains`: 选中的领域列表（可选）
- `tags`: 标签列表（可选）

**响应：** 同文档导入

---

## 7. 任务管理接口

### 7.1 查询任务状态
```
GET /tasks/{task_id}
```

**路径参数：**
- `task_id`: 任务ID

**响应示例：**
```json
{
  "task_id": "import_abc123",
  "status": "processing",
  "total_cases": 100,
  "processed_cases": 45,
  "stage": "classify",
  "stage_done": 20,
  "stage_total": 45,
  "overall_percent": 52.5,
  "stages": {
    "import": { "done": 45, "total": 100 },
    "classify": { "done": 20, "total": 45 },
    "kg_extract": { "done": 0, "total": 45 }
  },
  "current_case": "case_045",
  "current_action": "正在分类案例...",
  "progress_percent": 52.5,
  "result": null,
  "error_message": null,
  "created_at": "2026-04-08T10:00:00Z",
  "updated_at": "2026-04-08T10:05:30Z"
}
```

**任务状态说明：**
- `pending`: 等待中
- `processing`: 处理中
- `completed`: 已完成
- `failed`: 失败

**阶段说明：**
- `import`: 导入阶段（35% 权重）
- `classify`: AI 分类阶段（20% 权重）
- `kg_extract`: 知识图谱抽取阶段（45% 权重）

### 7.2 列出活跃任务
```
GET /tasks
```

**响应示例：**
```json
{
  "tasks": [
    {
      "task_id": "import_abc123",
      "status": "processing",
      "progress_percent": 52.5
    }
  ]
}
```

---

## 8. 决策记录接口

### 8.1 创建决策记录
```
POST /decisions
```

**请求体：**
```json
{
  "id": "dec_001",
  "query": "应该整体重构还是分阶段迁移？",
  "context": {
    "source": "web.query",
    "reasoning": "...",
    "recommendations": ["..."]
  },
  "recommended_cases": ["TEC-REF-001", "TEC-REF-002"],
  "choice": "分阶段迁移",
  "predict": "预计6个月完成"
}
```

**响应示例：**
```json
{
  "id": "dec_001"
}
```

### 8.2 评估决策结果
```
POST /decisions/{decision_id}/evaluate
```

**路径参数：**
- `decision_id`: 决策ID

**请求体：**
```json
{
  "outcome": "成功完成迁移，系统稳定性提升"
}
```

**响应示例：**
```json
{
  "id": "dec_001"
}
```

---

## 9. AI 配置接口

### 9.1 获取 AI 配置
```
GET /ai/config
```

**响应示例：**
```json
{
  "provider": "ollama",
  "model": "deepseek-r1:7b",
  "api_base": "http://localhost:11434",
  "api_key_set": false
}
```

### 9.2 更新 AI 配置
```
POST /ai/config
```

**请求体：**
```json
{
  "provider": "ollama",
  "model": "deepseek-r1:7b",
  "api_base": "http://localhost:11434",
  "api_key": ""
}
```

**响应示例：**
```json
{
  "status": "ok",
  "provider": "ollama",
  "model": "deepseek-r1:7b"
}
```

### 9.3 获取 AI 状态
```
GET /ai/status
```

**响应示例：**
```json
{
  "available": true,
  "provider": "ollama",
  "model": "deepseek-r1:7b"
}
```

---

## 10. GraphRAG 接口

### 10.1 构建向量索引
```
POST /graphrag/index
```

**请求体：**
```json
{
  "limit_cases": 0
}
```

**响应示例：**
```json
{
  "status": "ok",
  "indexed_cases": 128,
  "chunks_created": 512
}
```

### 10.2 获取 GraphRAG 状态
```
GET /graphrag/status
```

**响应示例：**
```json
{
  "qdrant_available": true,
  "collection_exists": true,
  "collection_vectors_count": 512,
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

---

## 附录：错误响应格式

所有接口在出错时返回标准 HTTP 错误码和错误信息：

```json
{
  "detail": "错误描述信息"
}
```

常见错误码：
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误
