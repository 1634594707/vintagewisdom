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

function apiBase(): string {
  return process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
}

async function fetchForm<T>(path: string, form: FormData): Promise<T> {
  const url = `${apiBase()}${path}`;
  const res = await fetch(url, {
    method: "POST",
    body: form,
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${res.statusText}: ${text}`);
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
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${res.statusText}: ${text}`);
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
