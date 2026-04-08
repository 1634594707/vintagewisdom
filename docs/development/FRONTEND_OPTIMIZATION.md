# 前端优化建议

## 概述

本文档针对 VintageWisdom 前端项目提出优化建议，包括 API 对接优化、性能提升、用户体验改进等方面。

---

## 1. API 对接优化

### 1.1 当前状态分析

**已实现的功能：**
- ✅ 基础 API 封装（`frontend/src/lib/api.ts`）
- ✅ 案例管理接口对接
- ✅ 决策查询接口对接
- ✅ 文件导入接口对接（CSV、JSON、Document）
- ✅ 异步任务轮询机制
- ✅ AI 自动分类接口对接
- ✅ 知识图谱接口对接

**待优化的问题：**
1. 缺少统一的错误处理机制
2. 没有请求重试逻辑
3. 缺少请求取消机制
4. 类型定义可以更完善
5. 缺少 API 响应缓存

### 1.2 优化方案

#### 1.2.1 统一错误处理

创建 `frontend/src/lib/api-error.ts`：

```typescript
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

#### 1.2.2 请求重试机制

创建 `frontend/src/lib/api-retry.ts`：

```typescript
export interface RetryOptions {
  maxRetries?: number;
  retryDelay?: number;
  retryOn?: (error: APIError) => boolean;
}

export async function fetchWithRetry<T>(
  fetcher: () => Promise<T>,
  options: RetryOptions = {}
): Promise<T> {
  const {
    maxRetries = 3,
    retryDelay = 1000,
    retryOn = (error) => error.isNetworkError(),
  } = options;

  let lastError: APIError | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fetcher();
    } catch (error) {
      if (error instanceof APIError) {
        lastError = error;
        
        // 如果不应该重试，直接抛出错误
        if (!retryOn(error) || attempt === maxRetries) {
          throw error;
        }

        // 等待后重试
        await new Promise(resolve => setTimeout(resolve, retryDelay * (attempt + 1)));
      } else {
        throw error;
      }
    }
  }

  throw lastError;
}
```

#### 1.2.3 请求取消机制

更新 `frontend/src/lib/api.ts`：

```typescript
export class APIClient {
  private abortControllers = new Map<string, AbortController>();

  async fetch<T>(
    path: string,
    init?: RequestInit,
    options?: { cancelKey?: string }
  ): Promise<T> {
    const url = `${apiBase()}${path}`;
    
    // 如果提供了 cancelKey，创建可取消的请求
    let signal: AbortSignal | undefined;
    if (options?.cancelKey) {
      // 取消之前的同名请求
      this.cancel(options.cancelKey);
      
      const controller = new AbortController();
      this.abortControllers.set(options.cancelKey, controller);
      signal = controller.signal;
    }

    try {
      const res = await fetch(url, {
        ...init,
        signal,
        headers: {
          'Content-Type': 'application/json',
          ...(init?.headers || {}),
        },
        cache: 'no-store',
      });

      if (!res.ok) {
        throw await APIError.fromResponse(res);
      }

      return (await res.json()) as T;
    } finally {
      if (options?.cancelKey) {
        this.abortControllers.delete(options.cancelKey);
      }
    }
  }

  cancel(key: string): void {
    const controller = this.abortControllers.get(key);
    if (controller) {
      controller.abort();
      this.abortControllers.delete(key);
    }
  }

  cancelAll(): void {
    this.abortControllers.forEach(controller => controller.abort());
    this.abortControllers.clear();
  }
}

export const apiClient = new APIClient();
```

#### 1.2.4 响应缓存机制

创建 `frontend/src/lib/api-cache.ts`：

```typescript
interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

export class APICache {
  private cache = new Map<string, CacheEntry<any>>();

  set<T>(key: string, data: T, ttl: number = 60000): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    });
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as T;
  }

  invalidate(key: string): void {
    this.cache.delete(key);
  }

  invalidatePrefix(prefix: string): void {
    for (const key of this.cache.keys()) {
      if (key.startsWith(prefix)) {
        this.cache.delete(key);
      }
    }
  }

  clear(): void {
    this.cache.clear();
  }
}

export const apiCache = new APICache();
```

---

## 2. 性能优化

### 2.1 图谱渲染优化

**当前问题：**
- 大规模图谱（>200 节点）渲染卡顿
- 缺少虚拟化和分页加载
- 没有节点聚合机制

**优化方案：**

#### 2.1.1 分批渲染

```typescript
// frontend/src/components/GraphView.tsx
export function GraphView({ data }: { data: GraphResponse }) {
  const [visibleNodes, setVisibleNodes] = useState<GraphNode[]>([]);
  const [batchIndex, setBatchIndex] = useState(0);
  const BATCH_SIZE = 50;

  useEffect(() => {
    // 分批加载节点
    const timer = setInterval(() => {
      if (batchIndex * BATCH_SIZE < data.nodes.length) {
        const nextBatch = data.nodes.slice(
          batchIndex * BATCH_SIZE,
          (batchIndex + 1) * BATCH_SIZE
        );
        setVisibleNodes(prev => [...prev, ...nextBatch]);
        setBatchIndex(prev => prev + 1);
      } else {
        clearInterval(timer);
      }
    }, 100);

    return () => clearInterval(timer);
  }, [data.nodes, batchIndex]);

  // 渲染逻辑...
}
```

#### 2.1.2 节点聚合

```typescript
// 当节点数量过多时，自动聚合同领域节点
function aggregateNodes(nodes: GraphNode[], threshold: number = 200): GraphNode[] {
  if (nodes.length <= threshold) return nodes;

  const domainGroups = new Map<string, GraphNode[]>();
  
  nodes.forEach(node => {
    if (node.type === 'case') {
      const domain = node.domain || 'unknown';
      if (!domainGroups.has(domain)) {
        domainGroups.set(domain, []);
      }
      domainGroups.get(domain)!.push(node);
    }
  });

  const aggregated: GraphNode[] = [];
  
  domainGroups.forEach((cases, domain) => {
    if (cases.length > 10) {
      // 创建聚合节点
      aggregated.push({
        id: `agg:${domain}`,
        type: 'aggregate',
        label: `${domain} (${cases.length} cases)`,
        domain,
        _aggregated: cases,
      });
    } else {
      aggregated.push(...cases);
    }
  });

  return aggregated;
}
```

### 2.2 列表虚拟化

**当前问题：**
- 案例列表在数据量大时渲染慢
- 滚动性能差

**优化方案：**

使用 `react-window` 或 `react-virtual` 实现虚拟滚动：

```typescript
import { FixedSizeList } from 'react-window';

export function CaseList({ cases }: { cases: Case[] }) {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const case_ = cases[index];
    return (
      <div style={style}>
        <CaseCard case={case_} />
      </div>
    );
  };

  return (
    <FixedSizeList
      height={600}
      itemCount={cases.length}
      itemSize={120}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
}
```

### 2.3 图片和资源优化

**优化方案：**

1. 使用 Next.js Image 组件
2. 启用图片懒加载
3. 使用 WebP 格式
4. 配置 CDN

```typescript
// next.config.ts
const config: NextConfig = {
  images: {
    formats: ['image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
};
```

---

## 3. 用户体验优化

### 3.1 加载状态优化

**当前问题：**
- 加载状态不够友好
- 缺少骨架屏
- 没有进度提示

**优化方案：**

#### 3.1.1 骨架屏组件

创建 `frontend/src/components/Skeleton.tsx`：

```typescript
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
```

#### 3.1.2 进度条组件

```typescript
export function ProgressBar({ 
  progress, 
  label, 
  showPercentage = true 
}: { 
  progress: number; 
  label?: string; 
  showPercentage?: boolean;
}) {
  const percentage = Math.max(0, Math.min(100, progress));

  return (
    <div>
      {label && (
        <div className="mb-2 flex items-center justify-between text-sm">
          <span className="text-[var(--text-secondary)]">{label}</span>
          {showPercentage && (
            <span className="vw-mono text-[var(--text-primary)]">{percentage}%</span>
          )}
        </div>
      )}
      <div className="h-3 rounded-full bg-[rgba(196,167,130,0.12)]">
        <div
          className="h-3 rounded-full bg-[linear-gradient(90deg,#a66d2b,#e0a652)] transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
```

### 3.2 错误处理优化

**当前问题：**
- 错误提示不够友好
- 缺少错误恢复机制
- 没有错误边界

**优化方案：**

#### 3.2.1 错误边界组件

创建 `frontend/src/components/ErrorBoundary.tsx`：

```typescript
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
          <div className="text-[var(--error)]">⚠️</div>
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

#### 3.2.2 友好的错误提示

```typescript
export function ErrorMessage({ error }: { error: APIError }) {
  const getMessage = () => {
    if (error.isNetworkError()) {
      return '网络连接失败，请检查后端服务是否启动';
    }
    if (error.isNotFound()) {
      return '请求的资源不存在';
    }
    if (error.isUnauthorized()) {
      return '未授权访问，请先登录';
    }
    return error.detail || error.message;
  };

  const getAction = () => {
    if (error.isNetworkError()) {
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

### 3.3 交互反馈优化

**优化方案：**

#### 3.3.1 Toast 通知

使用 `sonner` 或 `react-hot-toast`：

```typescript
import { toast } from 'sonner';

// 成功提示
toast.success('案例导入成功', {
  description: `已导入 ${imported} 条案例`,
});

// 错误提示
toast.error('导入失败', {
  description: error.message,
});

// 加载提示
const toastId = toast.loading('正在导入...');
// 完成后更新
toast.success('导入完成', { id: toastId });
```

#### 3.3.2 乐观更新

```typescript
export function useCases() {
  const [cases, setCases] = useState<Case[]>([]);

  const addCase = async (newCase: Case) => {
    // 乐观更新：立即添加到列表
    setCases(prev => [newCase, ...prev]);

    try {
      await api.createCase(newCase);
      toast.success('案例已添加');
    } catch (error) {
      // 失败时回滚
      setCases(prev => prev.filter(c => c.id !== newCase.id));
      toast.error('添加失败');
      throw error;
    }
  };

  return { cases, addCase };
}
```

---

## 4. 代码组织优化

### 4.1 自定义 Hooks

创建 `frontend/src/hooks/` 目录：

```typescript
// useAPI.ts
export function useAPI<T>(
  fetcher: () => Promise<T>,
  options?: {
    initialData?: T;
    revalidateOnFocus?: boolean;
  }
) {
  const [data, setData] = useState<T | undefined>(options?.initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<APIError | null>(null);

  const execute = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      setData(result);
      return result;
    } catch (err) {
      const apiError = err instanceof APIError ? err : new APIError(0, '', String(err), '');
      setError(apiError);
      throw apiError;
    } finally {
      setLoading(false);
    }
  }, [fetcher]);

  useEffect(() => {
    execute();
  }, [execute]);

  return { data, loading, error, refetch: execute };
}

// useCases.ts
export function useCases() {
  return useAPI(() => api.cases(), {
    revalidateOnFocus: true,
  });
}

// useTaskPolling.ts
export function useTaskPolling(taskId: string | null, interval: number = 1000) {
  const [status, setStatus] = useState<TaskStatusResponse | null>(null);
  const [error, setError] = useState<APIError | null>(null);

  useEffect(() => {
    if (!taskId) return;

    const poll = async () => {
      try {
        const result = await api.getTaskStatus(taskId);
        setStatus(result);

        if (result.status === 'completed' || result.status === 'failed') {
          return true; // 停止轮询
        }
      } catch (err) {
        setError(err instanceof APIError ? err : null);
        return true; // 出错时停止轮询
      }
      return false;
    };

    const timer = setInterval(async () => {
      const shouldStop = await poll();
      if (shouldStop) {
        clearInterval(timer);
      }
    }, interval);

    // 立即执行一次
    poll();

    return () => clearInterval(timer);
  }, [taskId, interval]);

  return { status, error };
}
```

### 4.2 Context 状态管理

创建 `frontend/src/contexts/AppContext.tsx`：

```typescript
'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

interface AppState {
  apiBase: string;
  degradedMode: boolean;
}

interface AppContextValue extends AppState {
  setDegradedMode: (degraded: boolean) => void;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState>({
    apiBase: process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000',
    degradedMode: false,
  });

  const setDegradedMode = (degraded: boolean) => {
    setState(prev => ({ ...prev, degradedMode: degraded }));
  };

  return (
    <AppContext.Provider value={{ ...state, setDegradedMode }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
}
```

---

## 5. 测试优化

### 5.1 单元测试

创建 `frontend/__tests__/lib/api.test.ts`：

```typescript
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

  it('should handle errors', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      text: async () => 'Not found',
    });

    await expect(api.case('invalid')).rejects.toThrow();
  });
});
```

### 5.2 E2E 测试

使用 Playwright：

```typescript
// e2e/query.spec.ts
import { test, expect } from '@playwright/test';

test('should perform query', async ({ page }) => {
  await page.goto('http://localhost:3000/query');
  
  await page.fill('textarea', '技术重构问题');
  await page.click('button:has-text("开始分析")');
  
  await expect(page.locator('text=正在检索历史回声')).toBeVisible();
  await expect(page.locator('text=相关案例')).toBeVisible({ timeout: 10000 });
});
```

---

## 6. 部署优化

### 6.1 构建优化

```typescript
// next.config.ts
const config: NextConfig = {
  // 启用 SWC 压缩
  swcMinify: true,
  
  // 分析包大小
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          default: false,
          vendors: false,
          // 第三方库单独打包
          vendor: {
            name: 'vendor',
            chunks: 'all',
            test: /node_modules/,
            priority: 20,
          },
          // 公共组件单独打包
          common: {
            name: 'common',
            minChunks: 2,
            chunks: 'all',
            priority: 10,
            reuseExistingChunk: true,
            enforce: true,
          },
        },
      };
    }
    return config;
  },
};
```

### 6.2 环境变量管理

创建 `.env.local.example`：

```bash
# API 配置
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000

# 功能开关
NEXT_PUBLIC_ENABLE_AI_CLUSTERING=true
NEXT_PUBLIC_ENABLE_GRAPHRAG=false

# 性能配置
NEXT_PUBLIC_GRAPH_MAX_NODES=300
NEXT_PUBLIC_GRAPH_MAX_EDGES=600
```

---

## 7. 实施优先级

### 高优先级（立即实施）
1. ✅ 统一错误处理机制
2. ✅ 请求重试逻辑
3. ✅ 骨架屏和加载状态
4. ✅ 错误边界组件

### 中优先级（近期实施）
1. 响应缓存机制
2. 列表虚拟化
3. 自定义 Hooks 封装
4. Toast 通知系统

### 低优先级（长期优化）
1. 图谱节点聚合
2. E2E 测试覆盖
3. 性能监控
4. PWA 支持

---

## 总结

通过以上优化，前端项目将在以下方面得到显著提升：

1. **稳定性**：统一的错误处理和重试机制
2. **性能**：虚拟化、缓存和分批渲染
3. **用户体验**：友好的加载状态和错误提示
4. **可维护性**：清晰的代码组织和类型定义
5. **可测试性**：完善的单元测试和 E2E 测试

建议按照优先级逐步实施，每个阶段完成后进行充分测试。
