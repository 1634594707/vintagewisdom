# 前后端对接快速实施指南

## 概述

本指南提供 VintageWisdom 前后端对接的快速实施步骤，帮助开发者快速上手并完成核心功能的对接。

---

## 第一阶段：基础设施搭建（1-2天）

### 1. 统一错误处理

#### 步骤 1：创建错误类型定义

```bash
# 创建文件
touch frontend/src/lib/api-error.ts
```

```typescript
// frontend/src/lib/api-error.ts
export class APIError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public detail: string,
    public url: string
  ) {
    super(`API ${status} ${statusText}: ${detail}`);
    this.name = 'APIError';
  }

  static async fromResponse(response: Response): Promise<APIError> {
    let detail = '';
    try {
      const data = await response.json();
      detail = data.detail || data.message || '';
    } catch {
      detail = await response.text().catch(() => '');
    }
    
    return new APIError(
      response.status,
      response.statusText,
      detail,
      response.url
    );
  }

  isNetworkError(): boolean {
    return this.status === 0 || this.status >= 500;
  }

  isClientError(): boolean {
    return this.status >= 400 && this.status < 500;
  }

  isNotFound(): boolean {
    return this.status === 404;
  }

  isUnauthorized(): boolean {
    return this.status === 401;
  }
}
```

#### 步骤 2：更新 API 客户端

```typescript
// frontend/src/lib/api.ts
import { APIError } from './api-error';

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${apiBase()}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    throw await APIError.fromResponse(res);
  }
  
  return (await res.json()) as T;
}
```

### 2. 创建通用组件

#### 步骤 1：错误提示组件

```bash
touch frontend/src/components/ErrorMessage.tsx
```

```typescript
// frontend/src/components/ErrorMessage.tsx
import { APIError } from '@/lib/api-error';

export function ErrorMessage({ error }: { error: APIError | Error | string }) {
  const getMessage = () => {
    if (typeof error === 'string') return error;
    if (error instanceof APIError) {
      if (error.isNetworkError()) {
        return '网络连接失败，请检查后端服务是否启动';
      }
      return error.detail || error.message;
    }
    return error.message;
  };

  const getAction = () => {
    if (error instanceof APIError && error.isNetworkError()) {
      return (
        <a
          href="http://127.0.0.1:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-[var(--accent-secondary)] hover:underline"
        >
          打开 API 文档检查
        </a>
      );
    }
    return null;
  };

  return (
    <div className="rounded-2xl border border-[color:rgba(239,68,68,0.28)] bg-[rgba(239,68,68,0.12)] p-4">
      <div className="flex items-start gap-3">
        <div className="text-[var(--error)]">⚠️</div>
        <div className="flex-1">
          <div className="text-sm font-medium text-[var(--error)]">
            {getMessage()}
          </div>
          {getAction() && (
            <div className="mt-2">{getAction()}</div>
          )}
        </div>
      </div>
    </div>
  );
}
```

#### 步骤 2：加载骨架屏组件

```bash
touch frontend/src/components/Skeleton.tsx
```

```typescript
// frontend/src/components/Skeleton.tsx
export function CaseCardSkeleton() {
  return (
    <div className="vw-card animate-pulse rounded-[24px] p-5">
      <div className="flex items-center gap-2">
        <div className="h-6 w-20 rounded-full bg-[rgba(196,167,130,0.12)]" />
        <div className="h-4 w-32 rounded bg-[rgba(196,167,130,0.08)]" />
      </div>
      <div className="mt-3 h-6 w-3/4 rounded bg-[rgba(196,167,130,0.12)]" />
      <div className="mt-2 space-y-2">
        <div className="h-4 w-full rounded bg-[rgba(196,167,130,0.08)]" />
        <div className="h-4 w-5/6 rounded bg-[rgba(196,167,130,0.08)]" />
      </div>
    </div>
  );
}

export function CaseListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <CaseCardSkeleton key={i} />
      ))}
    </div>
  );
}

export function GraphSkeleton() {
  return (
    <div className="vw-card animate-pulse rounded-[24px] p-5">
      <div className="h-[600px] rounded-2xl bg-[rgba(196,167,130,0.08)]" />
    </div>
  );
}
```

---

## 第二阶段：核心功能对接（3-5天）

### 1. 案例列表页优化

#### 步骤 1：创建案例列表 Hook

```bash
mkdir -p frontend/src/hooks
touch frontend/src/hooks/useCases.ts
```

```typescript
// frontend/src/hooks/useCases.ts
import { useState, useEffect } from 'react';
import { api, Case } from '@/lib/api';
import { APIError } from '@/lib/api-error';

export function useCases() {
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<APIError | null>(null);

  const fetchCases = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.cases();
      setCases(data);
    } catch (err) {
      setError(err instanceof APIError ? err : null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, []);

  return { cases, loading, error, refetch: fetchCases };
}
```

#### 步骤 2：更新案例列表页

```typescript
// frontend/src/app/cases/page.tsx
'use client';

import { useCases } from '@/hooks/useCases';
import { CaseListSkeleton } from '@/components/Skeleton';
import { ErrorMessage } from '@/components/ErrorMessage';
import AppShell from '@/components/AppShell';

export default function CasesPage() {
  const { cases, loading, error, refetch } = useCases();

  if (loading) {
    return (
      <AppShell title="案例库">
        <CaseListSkeleton count={5} />
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell title="案例库">
        <ErrorMessage error={error} />
        <button onClick={refetch} className="vw-btn-primary mt-4 px-4 py-2">
          重试
        </button>
      </AppShell>
    );
  }

  return (
    <AppShell title="案例库">
      <div className="space-y-4">
        {cases.map(case_ => (
          <CaseCard key={case_.id} case={case_} />
        ))}
      </div>
    </AppShell>
  );
}
```

### 2. 异步导入进度优化

#### 步骤 1：创建任务轮询 Hook

```bash
touch frontend/src/hooks/useTaskPolling.ts
```

```typescript
// frontend/src/hooks/useTaskPolling.ts
import { useState, useEffect, useRef } from 'react';
import { api, TaskStatusResponse } from '@/lib/api';
import { APIError } from '@/lib/api-error';

export function useTaskPolling(
  taskId: string | null,
  options: {
    interval?: number;
    onComplete?: (result: TaskStatusResponse) => void;
    onError?: (error: APIError) => void;
  } = {}
) {
  const { interval = 1000, onComplete, onError } = options;
  const [status, setStatus] = useState<TaskStatusResponse | null>(null);
  const [error, setError] = useState<APIError | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!taskId) return;

    const poll = async () => {
      try {
        const result = await api.getTaskStatus(taskId);
        setStatus(result);

        if (result.status === 'completed') {
          onComplete?.(result);
          return true; // 停止轮询
        }
        
        if (result.status === 'failed') {
          const err = new APIError(500, 'Task Failed', result.error_message || 'Unknown error', '');
          setError(err);
          onError?.(err);
          return true; // 停止轮询
        }
      } catch (err) {
        const apiError = err instanceof APIError ? err : new APIError(0, '', String(err), '');
        setError(apiError);
        onError?.(apiError);
        return true; // 出错时停止轮询
      }
      return false;
    };

    // 立即执行一次
    poll();

    // 设置定时轮询
    timerRef.current = setInterval(async () => {
      const shouldStop = await poll();
      if (shouldStop && timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }, interval);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [taskId, interval, onComplete, onError]);

  return { status, error };
}
```

#### 步骤 2：更新导入页面

```typescript
// frontend/src/app/import/page.tsx
import { useTaskPolling } from '@/hooks/useTaskPolling';

export default function ImportPage() {
  const [taskId, setTaskId] = useState<string | null>(null);
  
  const { status, error } = useTaskPolling(taskId, {
    interval: 1000,
    onComplete: (result) => {
      toast.success('导入完成', {
        description: `成功导入 ${result.result?.imported || 0} 条案例`,
      });
    },
    onError: (error) => {
      toast.error('导入失败', {
        description: error.detail,
      });
    },
  });

  // 其余代码...
}
```

### 3. 图谱性能优化

#### 步骤 1：添加节点过滤

```typescript
// frontend/src/components/GraphView.tsx
export function GraphView({ data }: { data: GraphResponse }) {
  const [filter, setFilter] = useState({
    domains: [] as string[],
    minSimilarity: 0.3,
    showClusters: true,
  });

  const filteredData = useMemo(() => {
    let nodes = data.nodes;
    let edges = data.edges;

    // 按领域过滤
    if (filter.domains.length > 0) {
      nodes = nodes.filter(n => 
        n.type === 'domain' || 
        (n.domain && filter.domains.includes(n.domain))
      );
      const nodeIds = new Set(nodes.map(n => n.id));
      edges = edges.filter(e => 
        nodeIds.has(e.source) && nodeIds.has(e.target)
      );
    }

    // 按相似度过滤
    edges = edges.filter(e => {
      if (e.edge_type === 'case_similar') {
        return (e.similarity || 0) >= filter.minSimilarity;
      }
      return true;
    });

    // 隐藏聚类
    if (!filter.showClusters) {
      nodes = nodes.filter(n => n.type !== 'cluster');
      edges = edges.filter(e => e.edge_type !== 'cluster_case');
    }

    return { nodes, edges };
  }, [data, filter]);

  return (
    <div>
      <GraphFilters filter={filter} onChange={setFilter} />
      <GraphCanvas data={filteredData} />
    </div>
  );
}
```

---

## 第三阶段：用户体验提升（2-3天）

### 1. 添加 Toast 通知

#### 步骤 1：安装依赖

```bash
cd frontend
pnpm add sonner
```

#### 步骤 2：配置 Toast Provider

```typescript
// frontend/src/app/layout.tsx
import { Toaster } from 'sonner';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        {children}
        <Toaster 
          position="top-right"
          toastOptions={{
            style: {
              background: 'var(--surface-primary)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border-subtle)',
            },
          }}
        />
      </body>
    </html>
  );
}
```

#### 步骤 3：使用 Toast

```typescript
import { toast } from 'sonner';

// 成功提示
toast.success('操作成功');

// 错误提示
toast.error('操作失败', {
  description: error.message,
});

// 加载提示
const toastId = toast.loading('正在处理...');
// 完成后更新
toast.success('处理完成', { id: toastId });
```

### 2. 添加错误边界

#### 步骤 1：创建错误边界组件

```bash
touch frontend/src/components/ErrorBoundary.tsx
```

```typescript
// frontend/src/components/ErrorBoundary.tsx
'use client';

import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="vw-panel rounded-[28px] p-8 text-center">
          <div className="text-4xl">⚠️</div>
          <h2 className="vw-title mt-4 text-2xl font-semibold">出错了</h2>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            {this.state.error?.message || '未知错误'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="vw-btn-primary mt-4 px-4 py-2 text-sm"
          >
            重试
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

#### 步骤 2：在布局中使用

```typescript
// frontend/src/app/layout.tsx
import { ErrorBoundary } from '@/components/ErrorBoundary';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
        <Toaster />
      </body>
    </html>
  );
}
```

---

## 第四阶段：测试与优化（2-3天）

### 1. 添加单元测试

#### 步骤 1：配置测试环境

```bash
cd frontend
pnpm add -D vitest @testing-library/react @testing-library/jest-dom
```

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

#### 步骤 2：编写测试

```typescript
// __tests__/lib/api.test.ts
import { describe, it, expect, vi } from 'vitest';
import { api } from '@/lib/api';

describe('API Client', () => {
  it('should fetch cases', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [{ id: 'test', title: 'Test Case' }],
    });

    const cases = await api.cases();
    expect(cases).toHaveLength(1);
    expect(cases[0].id).toBe('test');
  });
});
```

### 2. 性能监控

#### 步骤 1：添加性能指标

```typescript
// frontend/src/lib/performance.ts
export function measurePerformance(name: string, fn: () => void) {
  const start = performance.now();
  fn();
  const end = performance.now();
  console.log(`[Performance] ${name}: ${(end - start).toFixed(2)}ms`);
}

export function measureAsync<T>(name: string, fn: () => Promise<T>): Promise<T> {
  const start = performance.now();
  return fn().finally(() => {
    const end = performance.now();
    console.log(`[Performance] ${name}: ${(end - start).toFixed(2)}ms`);
  });
}
```

#### 步骤 2：使用性能监控

```typescript
import { measureAsync } from '@/lib/performance';

const cases = await measureAsync('Fetch Cases', () => api.cases());
```

---

## 验收清单

### 基础功能
- [ ] 后端 API 正常启动（http://127.0.0.1:8000）
- [ ] 前端正常启动（http://127.0.0.1:3000）
- [ ] 健康检查接口正常（/health）
- [ ] API 文档可访问（/docs）

### 案例管理
- [ ] 案例列表正常加载
- [ ] 案例详情页正常显示
- [ ] 相似案例推荐正常工作
- [ ] 案例搜索功能正常

### 决策查询
- [ ] 查询接口正常响应
- [ ] AI 推理结果正常显示
- [ ] 决策记录保存成功
- [ ] 历史查询可查看

### 文件导入
- [ ] CSV 导入成功
- [ ] JSON 异步导入成功
- [ ] 任务进度正常显示
- [ ] AI 自动分类正常工作
- [ ] PDF/DOCX 导入成功

### 知识图谱
- [ ] 图谱数据正常加载
- [ ] 节点和边正常渲染
- [ ] AI 聚类功能正常
- [ ] 相似度计算正确
- [ ] 图谱交互流畅

### 用户体验
- [ ] 加载状态友好
- [ ] 错误提示清晰
- [ ] Toast 通知正常
- [ ] 骨架屏显示正确
- [ ] 响应速度快

### 性能指标
- [ ] 首屏加载 < 2s
- [ ] API 响应 < 500ms
- [ ] 图谱渲染 < 1s
- [ ] 文件导入进度实时更新
- [ ] 无明显卡顿

---

## 常见问题排查

### 1. 后端连接失败

**症状：** 前端显示"网络连接失败"

**排查步骤：**
1. 检查后端是否启动：`curl http://127.0.0.1:8000/health`
2. 检查端口是否被占用：`lsof -i :8000`
3. 检查防火墙设置
4. 检查 CORS 配置

### 2. 导入任务卡住

**症状：** 导入进度停在某个百分比不动

**排查步骤：**
1. 检查后端日志：查看是否有错误
2. 检查数据库连接：确认 SQLite 文件可写
3. 检查 AI 服务：确认 Ollama 或 OpenAI 可用
4. 重启后端服务

### 3. 图谱渲染慢

**症状：** 图谱加载时间过长或卡顿

**排查步骤：**
1. 检查节点数量：超过 300 个考虑分页
2. 启用节点过滤：减少渲染数量
3. 调整相似度阈值：减少边的数量
4. 禁用 AI 聚类：如果不需要

### 4. AI 功能不可用

**症状：** 自动分类或聚类失败

**排查步骤：**
1. 检查 AI 配置：`GET /ai/config`
2. 检查 AI 状态：`GET /ai/status`
3. 测试 Ollama：`curl http://localhost:11434/api/tags`
4. 查看后端日志：确认错误信息

---

## 下一步

完成以上步骤后，你可以：

1. 阅读 [API_SPECIFICATION.md](../api/API_SPECIFICATION.md) 了解完整 API
2. 阅读 [FRONTEND_OPTIMIZATION.md](./FRONTEND_OPTIMIZATION.md) 进行深度优化
3. 参考 [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) 了解系统架构
4. 查看 [UI-DESIGN.md](../design/UI-DESIGN.md) 了解设计规范

祝开发顺利！🎉
