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

- `NEXT_PUBLIC_API_BASE`: 后端 API 地址，默认假设为 `http://127.0.0.1:8000`

## 说明

发布版已移除未使用的 ReactFlow 旧图谱实现，当前图谱页面统一使用 Sigma 版本组件。
