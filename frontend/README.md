# Frontend

前端基于 Next.js 16。

## 开发

```bash
pnpm install
pnpm dev
```

## 构建

```bash
pnpm build
pnpm start
```

## 环境变量

- `NEXT_PUBLIC_API_BASE`: （可选）浏览器端直接请求的 API 地址；未设置时默认使用同源 `/api`
- `API_BASE`: （推荐）Next.js 服务端代理目标地址；默认 `http://127.0.0.1:8000`

默认行为：前端请求 `/api/*`，再由 Next.js rewrite 转发到 `API_BASE`，避免线上误连 `127.0.0.1`。

## 说明

发布版已移除未使用的 ReactFlow 旧图谱实现，当前图谱页面统一使用 Sigma 版本组件。
