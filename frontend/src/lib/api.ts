import { APIError } from './api-error';

export type StatsResponse = {
  cases: number;
  decision_logs: number;
  evaluated_decision_logs: number;
};

export type Case = {
  id: string;
  domain: string;
  title: string;
  description?: string | null;
  decision_node?: string | null;
  action_taken?: string | null;
  outcome_result?: string | null;
  outcome_timeline?: string | null;
  lesson_core?: string | null;
  confidence?: string | null;
  tags?: string[];
  created_at?: string;
  updated_at?: string;
};

export type QueryResponse = {
  matches: number;
  cases: Case[];
  reasoning: string;
  recommendations: string[];
};

export type CreateDecisionRequest = {
  id?: string;
  query: string;
  context?: Record<string, unknown>;
  recommended_cases?: string[];
  choice?: string;
  predict?: string;
};

export type CreateDecisionResponse = {
  id: string;
};

export type GraphNode = {
  id: string;
  type: "domain" | "case" | "cluster" | string;
  label: string;
  domain?: string;
  case_id?: string;
  cluster_theme?: string;
  decision_node?: string;
  lesson_core?: string;
  attributes?: Record<string, unknown>;
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  type?: string;
  edge_type?: "domain_case" | "case_similar" | "cluster_case";
  similarity?: number;
  reasons?: string[];
  confidence?: number;
  attributes?: Record<string, unknown>;
  evidence?: {
    id: string;
    relation_id: string;
    case_id: string;
    quote: string;
    start_offset?: number | null;
    end_offset?: number | null;
    created_at?: string;
  }[];
};

export type ClusterInfo = {
  cluster_id: string;
  cluster_name: string;
  cases: string[];
  theme: string;
};

export type GraphResponse = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  clusters?: ClusterInfo[];
  stats?: {
    domain_count: number;
    case_count: number;
    similar_edge_count: number;
    cluster_count: number;
  };
};

export type KgNodeDetails = {
  id: string;
  type: string;
  label: string;
  attributes: Record<string, unknown>;
};

export type IngestCsvResponse = {
  status: string;
  sha256: string;
  imported?: number;
  skipped?: number;
  failed?: number;
  case_ids?: string[];
  message?: string;
  auto_classified?: boolean;
  suggested_domains?: string[];
};

export type IngestDocumentResponse = {
  status: string;
  sha256: string;
  case_id?: string;
  message?: string;
  auto_classified?: boolean;
  suggested_domains?: string[];
};

export type IngestJsonResponse = {
  status: string;
  sha256: string;
  imported?: number;
  skipped?: number;
  failed?: number;
  case_ids?: string[];
  message?: string;
  auto_classified?: boolean;
  suggested_domains?: string[];
};

// 异步导入响应
export type AsyncImportResponse = {
  status: string;
  task_id: string;
  total_cases: number;
  message: string;
};

// 任务状态响应
export type TaskStatusResponse = {
  task_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  total_cases: number;
  processed_cases: number;
  stage?: string;
  stage_done?: number;
  stage_total?: number;
  overall_percent?: number;
  stages?: {
    import?: { done: number; total: number };
    classify?: { done: number; total: number };
    kg_extract?: { done: number; total: number };
  };
  current_case?: string;
  current_action?: string;
  progress_percent: number;
  result?: {
    imported: number;
    skipped: number;
    failed: number;
    case_ids: string[];
    ai_classified?: boolean;
    ai_clustered?: boolean;
    kg_extracted?: boolean;
  };
  error_message?: string;
  created_at: string;
  updated_at: string;
};

// AI自动分类响应
export type AutoClassifyResponse = {
  suggestions: {
    domain: string;
    confidence: number;
    reason: string;
  }[];
};

// 相似案例响应
export type SimilarCasesResponse = {
  case_id: string;
  similar_cases: {
    case_id: string;
    similarity: number;
    reasons: string[];
  }[];
};

// AI配置响应
export type AIConfigResponse = {
  provider: string;
  model: string;
  api_base: string;
  api_key_set: boolean;
};

// AI状态响应
export type AIStatusResponse = {
  available: boolean;
  provider: string;
  model: string;
};

export const FALLBACK_CASES: Case[] = [
  {
    id: "TEC-REF-001",
    domain: "TEC-REF",
    title: "SaaS platform refactor under delivery pressure",
    description:
      "A team with rising incident load considered a full rewrite while enterprise commitments were still increasing.",
    decision_node: "Whether to freeze feature work and rebuild the core platform in one large move.",
    action_taken: "Protected the legacy core, launched new modules on a cleaner architecture, and moved capabilities gradually.",
    outcome_result: "Service quality improved without a full delivery stop. Migration was slower but much safer.",
    outcome_timeline: "6 to 12 months",
    lesson_core: "Prefer staged migration when technical debt is real but business continuity still matters.",
    confidence: "high",
    created_at: "2025-12-14",
    updated_at: "2026-03-29",
  },
  {
    id: "CAR-NEG-002",
    domain: "CAR-NEG",
    title: "Senior IC evaluating a high-cash offer versus long-term platform growth",
    description:
      "The candidate had a strong immediate offer, but the current company was entering a strategic expansion phase.",
    decision_node: "Take the external offer now or stay for a larger but uncertain upside.",
    action_taken: "Mapped downside scenarios, clarified role scope, and negotiated timeline flexibility before deciding.",
    outcome_result: "Decision quality improved because the choice was framed as portfolio risk, not just compensation.",
    outcome_timeline: "4 weeks",
    lesson_core: "Career decisions get clearer when role leverage, learning curve, and optionality are scored together.",
    confidence: "medium",
    created_at: "2026-01-11",
    updated_at: "2026-03-22",
  },
  {
    id: "HIS-POL-003",
    domain: "HIS-POL",
    title: "Reform initiative blocked by incumbent power groups",
    description:
      "A reform-minded leadership group underestimated how quickly existing institutions would coordinate resistance.",
    decision_node: "Push systemic reform immediately or build coalition capacity first.",
    action_taken: "Chose aggressive reform sequencing before durable support was built.",
    outcome_result: "Initial momentum was high, but implementation weakened once resistance consolidated.",
    outcome_timeline: "12 months",
    lesson_core: "Do not confuse policy clarity with execution capacity. Coalition readiness is part of the decision itself.",
    confidence: "high",
    created_at: "2026-01-07",
    updated_at: "2026-03-18",
  },
];

export const FALLBACK_STATS: StatsResponse = {
  cases: 128,
  decision_logs: 42,
  evaluated_decision_logs: 27,
};

export function isFetchFailure(error: unknown): boolean {
  return error instanceof Error && /fetch failed|ECONNREFUSED|ENOTFOUND|network/i.test(error.message);
}

function apiBase(): string {
  // 浏览器端可走同源 /api 代理；服务端必须使用绝对地址。
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_API_BASE || "/api";
  }
  return process.env.INTERNAL_API_BASE || process.env.API_BASE || process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
}

async function fetchForm<T>(path: string, form: FormData): Promise<T> {
  const url = `${apiBase()}${path}`;
  const res = await fetch(url, {
    method: "POST",
    body: form,
    cache: "no-store",
  });
  if (!res.ok) {
    throw await APIError.fromResponse(res);
  }
  return (await res.json()) as T;
}

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

export const api = {
  stats: () => fetchJson<StatsResponse>("/stats"),
  cases: () => fetchJson<Case[]>("/cases"),
  async case(id: string): Promise<Case> {
    return await fetchJson(`/cases/${encodeURIComponent(id)}`);
  },
  async kgNode(id: string): Promise<KgNodeDetails> {
    return await fetchJson(`/kg/node/${encodeURIComponent(id)}`);
  },
  graph: (path: string = "/graph") => fetchJson<GraphResponse>(path),
  
  // 增强的导入接口，支持AI自动分类
  ingestCsv: (file: File, opts?: { 
    default_domain?: string; 
    on_conflict?: "skip" | "replace";
    auto_classify?: boolean;
    domains?: string[];
    tags?: string[];
  }) => {
    const form = new FormData();
    form.append("file", file);
    if (opts?.default_domain) form.append("default_domain", opts.default_domain);
    if (opts?.on_conflict) form.append("on_conflict", opts.on_conflict);
    if (opts?.auto_classify !== undefined) form.append("auto_classify", String(opts.auto_classify));
    if (opts?.domains?.length) form.append("domains", JSON.stringify(opts.domains));
    if (opts?.tags?.length) form.append("tags", JSON.stringify(opts.tags));
    return fetchForm<IngestCsvResponse>("/ingest/csv", form);
  },
  
  ingestDocument: (
    file: File,
    opts?: { 
      doc_type?: "auto" | "pdf" | "docx"; 
      case_id?: string; 
      domain?: string; 
      title?: string;
      auto_classify?: boolean;
      domains?: string[];
      tags?: string[];
    }
  ) => {
    const form = new FormData();
    form.append("file", file);
    if (opts?.doc_type) form.append("doc_type", opts.doc_type);
    if (opts?.case_id) form.append("case_id", opts.case_id);
    if (opts?.domain) form.append("domain", opts.domain);
    if (opts?.title) form.append("title", opts.title);
    if (opts?.auto_classify !== undefined) form.append("auto_classify", String(opts.auto_classify));
    if (opts?.domains?.length) form.append("domains", JSON.stringify(opts.domains));
    if (opts?.tags?.length) form.append("tags", JSON.stringify(opts.tags));
    return fetchForm<IngestDocumentResponse>("/ingest/document", form);
  },
  
  ingestJson: (file: File, opts?: { 
    default_domain?: string; 
    on_conflict?: "skip" | "replace";
    auto_classify?: boolean;
    domains?: string[];
    tags?: string[];
  }) => {
    const form = new FormData();
    form.append("file", file);
    if (opts?.default_domain) form.append("default_domain", opts.default_domain);
    if (opts?.on_conflict) form.append("on_conflict", opts.on_conflict);
    if (opts?.auto_classify !== undefined) form.append("auto_classify", String(opts.auto_classify));
    if (opts?.domains?.length) form.append("domains", JSON.stringify(opts.domains));
    if (opts?.tags?.length) form.append("tags", JSON.stringify(opts.tags));
    return fetchForm<IngestJsonResponse>("/ingest/json", form);
  },
  
  // 异步 JSON 导入（支持 AI 分析和进度跟踪）
  ingestJsonAsync: (file: File, opts?: { 
    default_domain?: string; 
    auto_classify?: boolean;
    auto_cluster?: boolean;
    domains?: string[];
    tags?: string[];
  }) => {
    const form = new FormData();
    form.append("file", file);
    if (opts?.default_domain) form.append("default_domain", opts.default_domain);
    if (opts?.auto_classify !== undefined) form.append("auto_classify", String(opts.auto_classify));
    if (opts?.auto_cluster !== undefined) form.append("auto_cluster", String(opts.auto_cluster));
    if (opts?.domains?.length) form.append("domains", JSON.stringify(opts.domains));
    if (opts?.tags?.length) form.append("tags", JSON.stringify(opts.tags));
    return fetchForm<AsyncImportResponse>("/ingest/json/async", form);
  },
  
  // 查询导入任务状态
  getTaskStatus: (taskId: string) =>
    fetchJson<TaskStatusResponse>(`/tasks/${taskId}`),
  
  // AI自动分类接口
  autoClassify: (text: string) =>
    fetchJson<AutoClassifyResponse>("/classify", {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  
  // 获取相似案例
  getSimilarCases: (caseId: string, threshold?: number) =>
    fetchJson<SimilarCasesResponse>(`/cases/${caseId}/similar?threshold=${threshold || 0.3}`),
  
  query: (text: string) =>
    fetchJson<QueryResponse>("/query", {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  createDecision: (req: CreateDecisionRequest) =>
    fetchJson<CreateDecisionResponse>("/decisions", {
      method: "POST",
      body: JSON.stringify(req),
    }),
  
  // AI配置相关API
  getAIConfig: () => fetchJson<AIConfigResponse>("/ai/config"),
  getAIStatus: () => fetchJson<AIStatusResponse>("/ai/status"),
  updateAIConfig: (config: {
    provider: string;
    model: string;
    api_key?: string;
    api_base?: string;
  }) =>
    fetchJson<{ status: string; provider: string; model: string }>("/ai/config", {
      method: "POST",
      body: JSON.stringify(config),
    }),
};

// ========== 标签管理 API ==========

export type Tag = {
  id: string;
  name: string;
  case_count: number;
  created_at: string;
};

export type CaseTag = {
  id: string;
  name: string;
  created_at: string;
};

// ========== 案例版本历史 ==========

export type CaseVersion = {
  id: number;
  case_id: string;
  version_number: number;
  created_at: string;
};

// ========== 决策历史 ==========

export type DecisionLog = {
  id: string;
  query: string;
  context: Record<string, unknown>;
  recommended_cases: string[];
  user_decision?: string;
  predicted_outcome?: string;
  actual_outcome?: string;
  created_at: string;
  evaluated_at?: string;
};

// ========== 导出响应 ==========

export type ExportResponse = {
  format: string;
  export_time: string;
  count: number;
  data: unknown;
};

// 扩展API对象
export const apiExtended = {
  ...api,
  
  // 标签管理
  listTags: () => fetchJson<Tag[]>("/tags"),
  createTag: (name: string) => 
    fetchJson<{ id: string; name: string }>("/tags", {
      method: "POST",
      body: JSON.stringify(name),
    }),
  deleteTag: (tagId: string) =>
    fetchJson<{ status: string; id: string }>(`/tags/${tagId}`, {
      method: "DELETE",
    }),
  renameTag: (tagId: string, name: string) =>
    fetchJson<{ status: string; id: string; name: string }>(`/tags/${tagId}`, {
      method: "PUT",
      body: JSON.stringify(name),
    }),
  addCaseTag: (caseId: string, tagId: string) =>
    fetchJson<{ status: string }>(`/cases/${caseId}/tags/${tagId}`, {
      method: "POST",
    }),
  removeCaseTag: (caseId: string, tagId: string) =>
    fetchJson<{ status: string }>(`/cases/${caseId}/tags/${tagId}`, {
      method: "DELETE",
    }),
  getCaseTags: (caseId: string) =>
    fetchJson<CaseTag[]>(`/cases/${caseId}/tags`),
  
  // 案例编辑与版本历史
  updateCase: (caseId: string, data: Partial<Case>) =>
    fetchJson<{ status: string; id: string }>(`/cases/${caseId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  getCaseVersions: (caseId: string) =>
    fetchJson<CaseVersion[]>(`/cases/${caseId}/versions`),
  getCaseVersion: (caseId: string, versionNumber: number) =>
    fetchJson<Case>(`/cases/${caseId}/versions/${versionNumber}`),
  restoreCaseVersion: (caseId: string, versionNumber: number) =>
    fetchJson<{ status: string }>(`/cases/${caseId}/versions/${versionNumber}/restore`, {
      method: "POST",
    }),
  
  // 批量操作
  batchDeleteCases: (caseIds: string[]) =>
    fetchJson<{ status: string; count: number }>("/cases/batch/delete", {
      method: "POST",
      body: JSON.stringify(caseIds),
    }),
  batchAddTags: (caseIds: string[], tagIds: string[]) =>
    fetchJson<{ status: string; count: number }>("/cases/batch/tags/add", {
      method: "POST",
      body: JSON.stringify({ case_ids: caseIds, tag_ids: tagIds }),
    }),
  batchRemoveTags: (caseIds: string[], tagIds: string[]) =>
    fetchJson<{ status: string; count: number }>("/cases/batch/tags/remove", {
      method: "POST",
      body: JSON.stringify({ case_ids: caseIds, tag_ids: tagIds }),
    }),
  batchExportCases: (caseIds: string[], format: "json" | "csv" = "json") =>
    fetchJson<ExportResponse>("/cases/batch/export", {
      method: "POST",
      body: JSON.stringify({ case_ids: caseIds, format }),
    }),
  
  // 决策历史管理
  listDecisions: (limit: number = 100) =>
    fetchJson<DecisionLog[]>(`/decisions/list?limit=${limit}`),
  getDecision: (decisionId: string) =>
    fetchJson<DecisionLog>(`/decisions/${decisionId}`),
  deleteDecision: (decisionId: string) =>
    fetchJson<{ status: string }>(`/decisions/${decisionId}`, {
      method: "DELETE",
    }),
  searchDecisions: (query: string, limit: number = 50) =>
    fetchJson<DecisionLog[]>(`/decisions/search?q=${encodeURIComponent(query)}&limit=${limit}`),
  
  // 数据导出
  exportCases: (options?: {
    format?: "json" | "csv" | "markdown";
    domain?: string;
    tags?: string;
    start_date?: string;
    end_date?: string;
  }) => {
    const params = new URLSearchParams();
    if (options?.format) params.append("format", options.format);
    if (options?.domain) params.append("domain", options.domain);
    if (options?.tags) params.append("tags", options.tags);
    if (options?.start_date) params.append("start_date", options.start_date);
    if (options?.end_date) params.append("end_date", options.end_date);
    return fetchJson<ExportResponse>(`/export/cases?${params.toString()}`);
  },
  exportDecisions: (format: "json" | "markdown" = "json") =>
    fetchJson<ExportResponse>(`/export/decisions?format=${format}`),
  exportGraph: () =>
    fetchJson<ExportResponse>("/export/graph"),
};
