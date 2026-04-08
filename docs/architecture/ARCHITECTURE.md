# Architecture

## Top Level

- `src/vintagewisdom/cli`: CLI 入口和命令实现
- `src/vintagewisdom/web`: FastAPI 应用与接口层
- `src/vintagewisdom/core`: 应用装配、引擎、检索、推荐、事件
- `src/vintagewisdom/storage`: SQLite、任务、向量与图存储
- `src/vintagewisdom/models`: Pydantic 数据模型
- `src/vintagewisdom/plugins`: 内置插件
- `src/vintagewisdom/knowledge`: 领域映射、知识图谱与热点索引
- `src/vintagewisdom/ai`: AI 适配与辅助能力
- `frontend/src/app`: Next.js 路由页面
- `frontend/src/components`: 前端组件
- `tests/unit`: 后端单元测试

## Runtime Flow

1. `VintageWisdomApp` 初始化配置、数据库和插件。
2. `Engine` 负责案例写入、查询、推荐和决策闭环。
3. `web.app:create_app` 暴露 HTTP API，并接上图谱、AI、导入和导出能力。
4. 前端通过 `frontend/src/lib/api.ts` 调用后端接口。

## Release Scope

本次发布版收口后的原则：

- 删除示例素材和过程性文档
- 删除未使用前端组件与旧依赖
- 删除默认 demo 插件
- 删除与当前仓库状态不一致的部署脚本
- 保留可运行、可测试、可构建的主链路
