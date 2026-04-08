# Frontend

前端基于 Next.js 16。

启动方式:

```bash
pnpm install
pnpm dev
```

补充:

- `pnpm dev` 默认使用 `next dev --webpack`
- 如需手动尝试 Turbopack: `pnpm run dev:turbo`

默认读取后端:

```text
http://127.0.0.1:8000
```

如需修改:

```powershell
$env:NEXT_PUBLIC_API_BASE = "http://127.0.0.1:8000"
pnpm dev
```

更完整的项目启动说明请看根目录 [README.md](d:/Administrator/Desktop/Full%20Stack/VintageWisdom/README.md)。
