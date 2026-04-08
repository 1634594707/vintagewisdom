# API Specification

基础信息：

- Base URL: `http://127.0.0.1:8000`
- Swagger: `/docs`
- Health: `/health`

## System

### `GET /health`

返回服务健康状态。

### `GET /stats`

返回统计信息：

```json
{
  "cases": 0,
  "decision_logs": 0,
  "evaluated_decision_logs": 0
}
```

## Cases

### `GET /cases`

返回全部案例。

### `GET /cases/{case_id}`

返回单个案例详情。

### `GET /cases/{case_id}/similar`

基于阈值返回相似案例。

查询参数：

- `threshold`: 默认 `0.3`

### `PUT /cases/{case_id}`

更新案例。

### `GET /cases/{case_id}/versions`

返回案例版本列表。

### `GET /cases/{case_id}/versions/{version_number}`

返回指定版本。

### `POST /cases/{case_id}/versions/{version_number}/restore`

恢复到指定版本。

### `POST /cases/batch/delete`

批量删除案例。

### `POST /cases/batch/tags/add`

批量给案例添加标签。

### `POST /cases/batch/tags/remove`

批量移除标签。

### `POST /cases/batch/export`

批量导出案例，支持 `json` / `csv`。

## Query And Graph

### `POST /query`

执行决策查询。

### `POST /classify`

对文本进行领域分类。

### `GET /graph`

返回案例图谱或知识图谱。

常用查询参数：

- `view`: `case` 或 `kg`
- `q`
- `seed_entity_id`
- `relation_type`
- `depth`

## Decisions

### `POST /decisions`

创建决策记录。

### `POST /decisions/{decision_id}/evaluate`

补充实际结果，完成闭环评价。

### `GET /decisions/list`

返回决策历史。

### `GET /decisions/search`

搜索决策历史。

### `GET /decisions/{decision_id}`

返回单个决策记录。

### `DELETE /decisions/{decision_id}`

删除决策记录。

## Tags

### `GET /tags`

列出所有标签。

### `POST /tags`

创建标签。

### `PUT /tags/{tag_id}`

重命名标签。

### `DELETE /tags/{tag_id}`

删除标签。

### `POST /cases/{case_id}/tags/{tag_id}`

为案例添加标签。

### `DELETE /cases/{case_id}/tags/{tag_id}`

移除案例标签。

### `GET /cases/{case_id}/tags`

获取案例标签。

## Import And Tasks

### `POST /ingest/json/async`

异步导入 JSON。

### `POST /ingest/file`

上传文件导入。

### `GET /tasks/{task_id}`

查询异步任务状态。

## AI

### `GET /ai/config`

读取当前 AI 配置。

### `POST /ai/config`

更新 AI 配置。

### `GET /ai/status`

检查 AI 可用状态。

## Export

### `GET /export/cases`

导出案例，支持 `json` / `csv` / `markdown`。

### `GET /export/decisions`

导出决策历史。

### `GET /export/graph`

导出图谱 JSON。

## Debug

### `GET /debug/db`

返回当前数据库路径和基础统计，适合联调或定位环境问题。
