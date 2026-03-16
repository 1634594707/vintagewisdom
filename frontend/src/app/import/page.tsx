"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import AppShell from "@/components/AppShell";
import DomainSelector from "@/components/DomainSelector";
import { api, IngestCsvResponse, IngestDocumentResponse, IngestJsonResponse, TaskStatusResponse } from "@/lib/api";
import { autoClassifyDomain } from "@/lib/domains";

type Tab = "csv" | "document" | "json";

const STORAGE_PREFIX = "vintagewisdom_import_";

export default function ImportPage() {
  // 初始状态（用于 SSR）
  const [tab, setTab] = useState<Tab>("csv");

  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvFileName, setCsvFileName] = useState<string>("");
  const [csvDefaultDomain, setCsvDefaultDomain] = useState<string>("");
  const [csvConflict, setCsvConflict] = useState<"skip" | "replace">("skip");
  const [csvEnableAutoClassify, setCsvEnableAutoClassify] = useState<boolean>(true);
  const [csvSelectedDomains, setCsvSelectedDomains] = useState<string[]>([]);
  const [csvSelectedTags, setCsvSelectedTags] = useState<string[]>([]);

  const [docFile, setDocFile] = useState<File | null>(null);
  const [docFileName, setDocFileName] = useState<string>("");
  const [docType, setDocType] = useState<"auto" | "pdf" | "docx">("auto");
  const [docCaseId, setDocCaseId] = useState<string>("");
  const [docDomain, setDocDomain] = useState<string>("");
  const [docTitle, setDocTitle] = useState<string>("");
  const [docEnableAutoClassify, setDocEnableAutoClassify] = useState<boolean>(true);
  const [docSelectedDomains, setDocSelectedDomains] = useState<string[]>([]);
  const [docSelectedTags, setDocSelectedTags] = useState<string[]>([]);
  const [docPreviewText, setDocPreviewText] = useState<string>("");
  const [docAutoClassifyResult, setDocAutoClassifyResult] = useState<{ domain: string; confidence: number }[]>([]);

  const [jsonFile, setJsonFile] = useState<File | null>(null);
  const [jsonFileName, setJsonFileName] = useState<string>("");
  const [jsonDefaultDomain, setJsonDefaultDomain] = useState<string>("");
  const [jsonConflict, setJsonConflict] = useState<"skip" | "replace">("skip");
  const [jsonEnableAutoClassify, setJsonEnableAutoClassify] = useState<boolean>(true);
  const [jsonEnableAutoCluster, setJsonEnableAutoCluster] = useState<boolean>(true);
  const [jsonSelectedDomains, setJsonSelectedDomains] = useState<string[]>([]);
  const [jsonSelectedTags, setJsonSelectedTags] = useState<string[]>([]);
  
  // 异步导入状态
  const [asyncTaskId, setAsyncTaskId] = useState<string>("");
  const [taskStatus, setTaskStatus] = useState<TaskStatusResponse | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [importing, setImporting] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [csvResult, setCsvResult] = useState<IngestCsvResponse | null>(null);
  const [docResult, setDocResult] = useState<IngestDocumentResponse | null>(null);
  const [jsonResult, setJsonResult] = useState<IngestJsonResponse | null>(null);

  const [isHydrated, setIsHydrated] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 客户端 hydration 完成后恢复状态
  useEffect(() => {
    // 使用 requestAnimationFrame 避免在 effect 中直接调用 setState
    requestAnimationFrame(() => {
      try {
        const savedTab = localStorage.getItem(`${STORAGE_PREFIX}tab`) as Tab;
        if (savedTab) setTab(savedTab);

        // CSV
        const savedCsvFileName = localStorage.getItem(`${STORAGE_PREFIX}csv_fileName`);
        const savedCsvDefaultDomain = localStorage.getItem(`${STORAGE_PREFIX}csv_defaultDomain`);
        const savedCsvConflict = localStorage.getItem(`${STORAGE_PREFIX}csv_conflict`);
        const savedCsvEnableAutoClassify = localStorage.getItem(`${STORAGE_PREFIX}csv_enableAutoClassify`);
        const savedCsvSelectedDomains = localStorage.getItem(`${STORAGE_PREFIX}csv_selectedDomains`);
        const savedCsvSelectedTags = localStorage.getItem(`${STORAGE_PREFIX}csv_selectedTags`);

        if (savedCsvFileName) setCsvFileName(savedCsvFileName);
        if (savedCsvDefaultDomain) setCsvDefaultDomain(savedCsvDefaultDomain);
        if (savedCsvConflict) setCsvConflict(savedCsvConflict as "skip" | "replace");
        if (savedCsvEnableAutoClassify) setCsvEnableAutoClassify(savedCsvEnableAutoClassify === "true");
        if (savedCsvSelectedDomains) {
          try { setCsvSelectedDomains(JSON.parse(savedCsvSelectedDomains)); } catch {}
        }
        if (savedCsvSelectedTags) {
          try { setCsvSelectedTags(JSON.parse(savedCsvSelectedTags)); } catch {}
        }

        // JSON
        const savedJsonFileName = localStorage.getItem(`${STORAGE_PREFIX}json_fileName`);
        const savedJsonDefaultDomain = localStorage.getItem(`${STORAGE_PREFIX}json_defaultDomain`);
        const savedJsonConflict = localStorage.getItem(`${STORAGE_PREFIX}json_conflict`);
        const savedJsonEnableAutoClassify = localStorage.getItem(`${STORAGE_PREFIX}json_enableAutoClassify`);
        const savedJsonSelectedDomains = localStorage.getItem(`${STORAGE_PREFIX}json_selectedDomains`);
        const savedJsonSelectedTags = localStorage.getItem(`${STORAGE_PREFIX}json_selectedTags`);

        if (savedJsonFileName) setJsonFileName(savedJsonFileName);
        if (savedJsonDefaultDomain) setJsonDefaultDomain(savedJsonDefaultDomain);
        if (savedJsonConflict) setJsonConflict(savedJsonConflict as "skip" | "replace");
        if (savedJsonEnableAutoClassify) setJsonEnableAutoClassify(savedJsonEnableAutoClassify === "true");
        if (savedJsonSelectedDomains) {
          try { setJsonSelectedDomains(JSON.parse(savedJsonSelectedDomains)); } catch {}
        }
        if (savedJsonSelectedTags) {
          try { setJsonSelectedTags(JSON.parse(savedJsonSelectedTags)); } catch {}
        }

        // Document
        const savedDocFileName = localStorage.getItem(`${STORAGE_PREFIX}doc_fileName`);
        const savedDocType = localStorage.getItem(`${STORAGE_PREFIX}doc_type`);
        const savedDocCaseId = localStorage.getItem(`${STORAGE_PREFIX}doc_caseId`);
        const savedDocDomain = localStorage.getItem(`${STORAGE_PREFIX}doc_domain`);
        const savedDocTitle = localStorage.getItem(`${STORAGE_PREFIX}doc_title`);
        const savedDocEnableAutoClassify = localStorage.getItem(`${STORAGE_PREFIX}doc_enableAutoClassify`);
        const savedDocSelectedDomains = localStorage.getItem(`${STORAGE_PREFIX}doc_selectedDomains`);
        const savedDocSelectedTags = localStorage.getItem(`${STORAGE_PREFIX}doc_selectedTags`);

        if (savedDocFileName) setDocFileName(savedDocFileName);
        if (savedDocType) setDocType(savedDocType as "auto" | "pdf" | "docx");
        if (savedDocCaseId) setDocCaseId(savedDocCaseId);
        if (savedDocDomain) setDocDomain(savedDocDomain);
        if (savedDocTitle) setDocTitle(savedDocTitle);
        if (savedDocEnableAutoClassify) setDocEnableAutoClassify(savedDocEnableAutoClassify === "true");
        if (savedDocSelectedDomains) {
          try { setDocSelectedDomains(JSON.parse(savedDocSelectedDomains)); } catch {}
        }
        if (savedDocSelectedTags) {
          try { setDocSelectedTags(JSON.parse(savedDocSelectedTags)); } catch {}
        }
      } catch (e) {
        console.error("Failed to restore state:", e);
      }
      setIsHydrated(true);
    });
  }, []);

  // 保存状态到 localStorage
  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}tab`, tab);
  }, [tab, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}csv_fileName`, csvFileName);
  }, [csvFileName, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}csv_defaultDomain`, csvDefaultDomain);
  }, [csvDefaultDomain, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}csv_conflict`, csvConflict);
  }, [csvConflict, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}csv_enableAutoClassify`, csvEnableAutoClassify.toString());
  }, [csvEnableAutoClassify, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}csv_selectedDomains`, JSON.stringify(csvSelectedDomains));
  }, [csvSelectedDomains, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}csv_selectedTags`, JSON.stringify(csvSelectedTags));
  }, [csvSelectedTags, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}json_fileName`, jsonFileName);
  }, [jsonFileName, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}json_defaultDomain`, jsonDefaultDomain);
  }, [jsonDefaultDomain, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}json_conflict`, jsonConflict);
  }, [jsonConflict, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}json_enableAutoClassify`, jsonEnableAutoClassify.toString());
  }, [jsonEnableAutoClassify, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}json_selectedDomains`, JSON.stringify(jsonSelectedDomains));
  }, [jsonSelectedDomains, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}json_selectedTags`, JSON.stringify(jsonSelectedTags));
  }, [jsonSelectedTags, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}doc_fileName`, docFileName);
  }, [docFileName, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}doc_type`, docType);
  }, [docType, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}doc_caseId`, docCaseId);
  }, [docCaseId, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}doc_domain`, docDomain);
  }, [docDomain, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}doc_title`, docTitle);
  }, [docTitle, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}doc_enableAutoClassify`, docEnableAutoClassify.toString());
  }, [docEnableAutoClassify, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}doc_selectedDomains`, JSON.stringify(docSelectedDomains));
  }, [docSelectedDomains, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(`${STORAGE_PREFIX}doc_selectedTags`, JSON.stringify(docSelectedTags));
  }, [docSelectedTags, isHydrated]);

  const selectedFileName = useMemo(() => {
    if (tab === "csv") return csvFileName;
    if (tab === "json") return jsonFileName;
    return docFileName;
  }, [csvFileName, docFileName, jsonFileName, tab]);

  const uploadDisabledReason = useMemo(() => {
    if (importing) return "正在导入中";
    if (tab === "csv" && !csvFile) return "请先选择 CSV 文件";
    if (tab === "json" && !jsonFile) return "请先选择 JSON 文件";
    if (tab === "document" && !docFile) return "请先选择 PDF/DOCX 文件";
    return "";
  }, [csvFile, docFile, importing, jsonFile, tab]);

  const accept = useMemo(() => {
    if (tab === "csv") return ".csv,text/csv";
    if (tab === "json") return ".json,application/json";
    return ".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document";
  }, [tab]);

  // 处理文档文件选择，进行AI自动分类预览
  const handleDocFileChange = async (file: File | null) => {
    setDocFile(file);
    setDocFileName(file?.name || "");
    setDocPreviewText("");
    setDocAutoClassifyResult([]);

    if (file && docEnableAutoClassify) {
      try {
        const text = await file.text();
        const preview = text.slice(0, 1000);
        setDocPreviewText(preview);

        const results = autoClassifyDomain(preview);
        setDocAutoClassifyResult(results);

        if (results.length > 0 && results[0].confidence > 0.5) {
          setDocSelectedDomains([results[0].domain]);
        }
      } catch {
        // 忽略预览错误
      }
    }
  };

  // 处理文件选择
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] || null;
    if (tab === "csv") {
      setCsvFile(f);
      setCsvFileName(f?.name || "");
    } else if (tab === "json") {
      setJsonFile(f);
      setJsonFileName(f?.name || "");
    } else {
      handleDocFileChange(f);
    }
  };

  async function onUpload() {
    setError("");
    setCsvResult(null);
    setDocResult(null);
    setJsonResult(null);
    setImporting(true);
    setLoading(true);

    try {
      if (tab === "csv") {
        if (!csvFile) return;
        const resp = await api.ingestCsv(csvFile, {
          default_domain: csvDefaultDomain || undefined,
          on_conflict: csvConflict,
          auto_classify: csvEnableAutoClassify,
          domains: csvSelectedDomains.length > 0 ? csvSelectedDomains : undefined,
          tags: csvSelectedTags.length > 0 ? csvSelectedTags : undefined,
        });
        setCsvResult(resp);
      } else if (tab === "json") {
        if (!jsonFile) return;
        
        // 使用异步导入
        const asyncResp = await api.ingestJsonAsync(jsonFile, {
          default_domain: jsonDefaultDomain || undefined,
          auto_classify: jsonEnableAutoClassify,
          auto_cluster: jsonEnableAutoCluster,
          domains: jsonSelectedDomains.length > 0 ? jsonSelectedDomains : undefined,
          tags: jsonSelectedTags.length > 0 ? jsonSelectedTags : undefined,
        });
        
        setAsyncTaskId(asyncResp.task_id);
        
        // 开始轮询任务状态
        const interval = setInterval(async () => {
          try {
            const status = await api.getTaskStatus(asyncResp.task_id);
            setTaskStatus(status);
            
            // 如果任务完成或失败，停止轮询
            if (status.status === "completed" || status.status === "failed") {
              if (interval) clearInterval(interval);
              setPollingInterval(null);
              setLoading(false);
              setImporting(false); // 异步导入完成，关闭导入中状态
              
              // 设置结果
              if (status.result) {
                setJsonResult({
                  status: status.status,
                  sha256: "",
                  imported: status.result.imported,
                  skipped: status.result.skipped,
                  failed: status.result.failed,
                  case_ids: status.result.case_ids,
                  auto_classified: status.result.ai_classified,
                });
              }
            }
          } catch (e) {
            console.error("Failed to get task status:", e);
          }
        }, 1000); // 每1秒查询一次，更实时
        
        setPollingInterval(interval);
        // 异步导入不立即结束 loading，等待轮询完成
      } else {
        if (!docFile) return;
        const resp = await api.ingestDocument(docFile, {
          doc_type: docType,
          case_id: docCaseId || undefined,
          domain: docDomain || (docSelectedDomains.length > 0 ? docSelectedDomains[0] : undefined),
          title: docTitle || undefined,
          auto_classify: docEnableAutoClassify,
          domains: docSelectedDomains.length > 0 ? docSelectedDomains : undefined,
          tags: docSelectedTags.length > 0 ? docSelectedTags : undefined,
        });
        setDocResult(resp);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setLoading(false);
      setImporting(false);
    }
    // 注意：异步导入的 importing 状态在轮询完成时处理
  }

  function onClear() {
    setCsvFile(null);
    setCsvFileName("");
    setCsvDefaultDomain("");
    setCsvConflict("skip");
    setCsvEnableAutoClassify(true);
    setCsvSelectedDomains([]);
    setCsvSelectedTags([]);
    setCsvResult(null);

    setJsonFile(null);
    setJsonFileName("");
    setJsonDefaultDomain("");
    setJsonConflict("skip");
    setJsonEnableAutoClassify(true);
    setJsonSelectedDomains([]);
    setJsonSelectedTags([]);
    setJsonResult(null);

    setDocFile(null);
    setDocFileName("");
    setDocType("auto");
    setDocCaseId("");
    setDocDomain("");
    setDocTitle("");
    setDocEnableAutoClassify(true);
    setDocSelectedDomains([]);
    setDocSelectedTags([]);
    setDocPreviewText("");
    setDocAutoClassifyResult([]);
    setDocResult(null);

    setError("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }

    Object.keys(localStorage)
      .filter((key) => key.startsWith(STORAGE_PREFIX))
      .forEach((key) => localStorage.removeItem(key));
  }

  function switchTab(newTab: Tab) {
    setTab(newTab);
    setError("");
  }

  // 导入中界面 - 显示进度
  // 条件：正在导入中，或者是JSON异步导入且任务未完成
  const isAsyncProcessing = tab === "json" && asyncTaskId && taskStatus && 
    taskStatus.status !== "completed" && taskStatus.status !== "failed";
  
  if (importing || isAsyncProcessing) {
    const isAsync = tab === "json" && asyncTaskId;
    const rawProgress = taskStatus?.overall_percent ?? taskStatus?.progress_percent ?? 0;
    const clampedProgress = Math.max(0, Math.min(100, rawProgress));
    const stage = taskStatus?.stage || "";
    const stages = taskStatus?.stages;
    
    return (
      <AppShell title="导入">
        <div className="flex h-[calc(100vh-120px)] flex-col items-center justify-center">
          <div className="relative">
            <div className="h-24 w-24 animate-spin rounded-full border-4 border-[var(--bg-tertiary)] border-t-[var(--accent-primary)]" />
            <div
              className="absolute inset-0 m-4 animate-spin rounded-full border-4 border-[var(--bg-tertiary)] border-b-[var(--accent-primary)]"
              style={{ animationDirection: "reverse", animationDuration: "1.5s" }}
            />
          </div>
          <div className="mt-8 text-center">
            <div className="text-lg font-medium text-[var(--text-primary)]">
              {isAsync ? "后台导入中..." : "正在导入..."}
            </div>
            <div className="mt-2 text-sm text-[var(--text-muted)]">
              {tab === "csv" && csvFileName && `CSV: ${csvFileName}`}
              {tab === "json" && jsonFileName && `JSON: ${jsonFileName}`}
              {tab === "document" && docFileName && `文档: ${docFileName}`}
            </div>
          </div>
          
          {/* 异步导入进度显示 */}
          {isAsync && (
            <div className="mt-8 w-full max-w-md space-y-4 px-4">
              {/* 进度条 */}
              <div className="rounded-xl border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-[var(--text-primary)]">导入进度</span>
                  <span className="text-sm font-semibold text-[var(--accent-primary)]">{clampedProgress.toFixed(1)}%</span>
                </div>
                <div className="h-2.5 rounded-full bg-[var(--bg-tertiary)] overflow-hidden">
                  <div 
                    className="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-500 ease-out"
                    style={{ width: `${Math.max(5, clampedProgress)}%` }}
                  />
                </div>
                <div className="mt-2 flex justify-between text-xs text-[var(--text-muted)]">
                  <span>{taskStatus?.processed_cases || 0} / {taskStatus?.total_cases || 0} 个案例</span>
                  <span>{taskStatus?.status === "pending" ? "等待中" : taskStatus?.status === "processing" ? "处理中" : "-"}</span>
                </div>
              </div>

              {/* 分阶段进度 */}
              {stages ? (
                <div className="rounded-xl border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-4">
                  <div className="text-xs font-medium text-[var(--text-primary)] mb-2">阶段进度</div>
                  <div className="space-y-1 text-xs text-[var(--text-muted)]">
                    <div className={stage === "import" ? "text-[var(--accent-primary)]" : ""}>
                      导入: {stages.import?.done ?? 0} / {stages.import?.total ?? 0}
                    </div>
                    <div className={stage === "classify" ? "text-[var(--accent-primary)]" : ""}>
                      AI分类: {stages.classify?.done ?? 0} / {stages.classify?.total ?? 0}
                    </div>
                    <div className={stage === "kg_extract" ? "text-[var(--accent-primary)]" : ""}>
                      KG抽取: {stages.kg_extract?.done ?? 0} / {stages.kg_extract?.total ?? 0}
                    </div>
                  </div>
                </div>
              ) : null}
              
              {/* 当前操作 */}
              {(taskStatus?.current_action || taskStatus?.current_case) && (
                <div className="rounded-xl border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-4">
                  <div className="flex items-center gap-2">
                    <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-[var(--accent-primary)]" />
                    <span className="text-sm text-[var(--text-primary)]">
                      {taskStatus?.current_action || "处理中..."}
                    </span>
                  </div>
                  {taskStatus?.current_case && (
                    <div className="mt-2 text-xs text-[var(--text-muted)] truncate font-mono bg-[var(--bg-primary)] px-2 py-1 rounded">
                      {taskStatus.current_case}
                    </div>
                  )}
                </div>
              )}
              
              {/* 任务状态 */}
              <div className="rounded-xl border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-4">
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="text-[var(--text-muted)]">任务ID</span>
                  <span className="font-mono text-[var(--text-secondary)] bg-[var(--bg-primary)] px-2 py-0.5 rounded">{asyncTaskId}</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[var(--text-muted)]">状态</span>
                  <span className={
                    taskStatus?.status === "completed" ? "text-green-400" :
                    taskStatus?.status === "failed" ? "text-red-400" :
                    "text-[var(--accent-primary)]"
                  }>
                    {taskStatus?.status === "pending" && "⏳ 等待中"}
                    {taskStatus?.status === "processing" && "🔄 处理中"}
                    {taskStatus?.status === "completed" && "✅ 已完成"}
                    {taskStatus?.status === "failed" && "❌ 失败"}
                    {!taskStatus && "初始化中..."}
                  </span>
                </div>
              </div>

              {/* 结果预览 */}
              {taskStatus?.result && (
                <div className="rounded-xl border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-4">
                  <div className="text-xs font-medium text-[var(--text-primary)] mb-2">处理结果</div>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="rounded-lg bg-[var(--bg-primary)] p-2">
                      <div className="text-lg font-semibold text-green-400">{taskStatus.result.imported}</div>
                      <div className="text-[10px] text-[var(--text-muted)]">成功</div>
                    </div>
                    <div className="rounded-lg bg-[var(--bg-primary)] p-2">
                      <div className="text-lg font-semibold text-yellow-400">{taskStatus.result.skipped}</div>
                      <div className="text-[10px] text-[var(--text-muted)]">跳过</div>
                    </div>
                    <div className="rounded-lg bg-[var(--bg-primary)] p-2">
                      <div className="text-lg font-semibold text-red-400">{taskStatus.result.failed}</div>
                      <div className="text-[10px] text-[var(--text-muted)]">失败</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* 普通导入状态 */}
          {!isAsync && (
            <div className="mt-8 max-w-md rounded-xl border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-4">
              <div className="text-xs text-[var(--text-muted)]">正在处理数据，请稍候...</div>
              {csvEnableAutoClassify && tab === "csv" && (
                <div className="mt-1 text-xs text-[var(--accent-primary)]">🤖 启用 AI 自动分类</div>
              )}
              {jsonEnableAutoClassify && tab === "json" && (
                <div className="mt-1 text-xs text-[var(--accent-primary)]">🤖 启用 AI 自动分类</div>
              )}
              {docEnableAutoClassify && tab === "document" && (
                <div className="mt-1 text-xs text-[var(--accent-primary)]">🤖 启用 AI 自动分类</div>
              )}
            </div>
          )}
        </div>
      </AppShell>
    );
  }

  // 显示结果界面
  if (csvResult || jsonResult || docResult) {
    const result = csvResult || jsonResult || docResult;
    const resultTitle = csvResult ? "CSV 导入成功" : jsonResult ? "JSON 导入成功" : "文档导入成功";

    return (
      <AppShell title="导入">
        <div className="space-y-6">
          <div className="flex items-center justify-between rounded-lg border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] px-4 py-3">
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-green-400">✓ {resultTitle}</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  setCsvResult(null);
                  setJsonResult(null);
                  setDocResult(null);
                }}
                className="rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] px-3 py-1.5 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              >
                继续导入
              </button>
              <button
                type="button"
                onClick={onClear}
                className="rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] px-3 py-1.5 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              >
                清除全部
              </button>
            </div>
          </div>

          <div className="rounded-lg border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-6">
            <div className="text-sm font-medium mb-4">导入结果详情</div>
            <pre className="whitespace-pre-wrap break-words rounded-md bg-[var(--bg-primary)] px-4 py-3 text-sm text-[var(--text-secondary)]">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>

          <div className="text-xs text-[var(--text-muted)]">
            导入完成后可前往「案例库 / 知识图谱」刷新查看。
          </div>
        </div>
      </AppShell>
    );
  }

  // 主界面
  return (
    <AppShell title="导入">
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => switchTab("csv")}
            className={
              tab === "csv"
                ? "rounded-md bg-[var(--accent-primary)] px-3 py-1.5 text-sm text-white"
                : "rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] px-3 py-1.5 text-sm text-[var(--text-secondary)]"
            }
          >
            CSV
          </button>
          <button
            type="button"
            onClick={() => switchTab("document")}
            className={
              tab === "document"
                ? "rounded-md bg-[var(--accent-primary)] px-3 py-1.5 text-sm text-white"
                : "rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] px-3 py-1.5 text-sm text-[var(--text-secondary)]"
            }
          >
            PDF / Word
          </button>
          <button
            type="button"
            onClick={() => switchTab("json")}
            className={
              tab === "json"
                ? "rounded-md bg-[var(--accent-primary)] px-3 py-1.5 text-sm text-white"
                : "rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] px-3 py-1.5 text-sm text-[var(--text-secondary)]"
            }
          >
            JSON
          </button>
        </div>

        <div className="rounded-lg border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-6">
          <div className="text-sm text-[var(--text-secondary)]">选择文件上传后导入到本地数据库。</div>

          <div className="mt-4 grid gap-4">
            <input
              ref={fileInputRef}
              type="file"
              accept={accept}
              onChange={handleFileChange}
              className="block w-full text-sm text-[var(--text-secondary)]"
            />

            <div className="text-xs text-[var(--text-muted)]">
              已选择：{selectedFileName || "（未选择）"}
            </div>

            {tab === "csv" ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  <div>
                    <div className="text-xs text-[var(--text-muted)]">默认领域（可选）</div>
                    <input
                      value={csvDefaultDomain}
                      onChange={(e) => setCsvDefaultDomain(e.target.value)}
                      className="mt-1 w-full rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                      placeholder="例如：CAR-JOB / FIN-INV"
                    />
                  </div>
                  <div>
                    <div className="text-xs text-[var(--text-muted)]">ID 冲突处理</div>
                    <select
                      value={csvConflict}
                      onChange={(e) => setCsvConflict(e.target.value as "skip" | "replace")}
                      className="mt-1 w-full rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                    >
                      <option value="skip">跳过</option>
                      <option value="replace">覆盖</option>
                    </select>
                  </div>
                </div>
                <DomainSelector
                  selectedDomains={csvSelectedDomains}
                  onChange={setCsvSelectedDomains}
                  selectedTags={csvSelectedTags}
                  onTagsChange={setCsvSelectedTags}
                  enableAutoClassify={csvEnableAutoClassify}
                  onAutoClassifyChange={setCsvEnableAutoClassify}
                />
              </div>
            ) : tab === "json" ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  <div>
                    <div className="text-xs text-[var(--text-muted)]">默认领域（可选）</div>
                    <input
                      value={jsonDefaultDomain}
                      onChange={(e) => setJsonDefaultDomain(e.target.value)}
                      className="mt-1 w-full rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                      placeholder="例如：FIN-INV"
                    />
                  </div>
                  <div>
                    <div className="text-xs text-[var(--text-muted)]">ID 冲突处理</div>
                    <select
                      value={jsonConflict}
                      onChange={(e) => setJsonConflict(e.target.value as "skip" | "replace")}
                      className="mt-1 w-full rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                    >
                      <option value="skip">跳过</option>
                      <option value="replace">覆盖</option>
                    </select>
                  </div>
                </div>
                <DomainSelector
                  selectedDomains={jsonSelectedDomains}
                  onChange={setJsonSelectedDomains}
                  selectedTags={jsonSelectedTags}
                  onTagsChange={setJsonSelectedTags}
                  enableAutoClassify={jsonEnableAutoClassify}
                  onAutoClassifyChange={setJsonEnableAutoClassify}
                />
                <div className="flex items-center gap-2 mt-2">
                  <input
                    type="checkbox"
                    id="json-auto-cluster"
                    checked={jsonEnableAutoCluster}
                    onChange={(e) => setJsonEnableAutoCluster(e.target.checked)}
                    className="rounded"
                  />
                  <label htmlFor="json-auto-cluster" className="text-sm text-[var(--text-secondary)]">
                    启用 AI 自动聚类（分析案例相似性并分组）
                  </label>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  <div>
                    <div className="text-xs text-[var(--text-muted)]">类型</div>
                    <select
                      value={docType}
                      onChange={(e) => setDocType(e.target.value as "auto" | "pdf" | "docx")}
                      className="mt-1 w-full rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                    >
                      <option value="auto">自动识别</option>
                      <option value="pdf">PDF</option>
                      <option value="docx">DOCX</option>
                    </select>
                  </div>
                  <div>
                    <div className="text-xs text-[var(--text-muted)]">Case ID（可选）</div>
                    <input
                      value={docCaseId}
                      onChange={(e) => setDocCaseId(e.target.value)}
                      className="mt-1 w-full rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                      placeholder="留空则自动生成"
                    />
                  </div>
                  <div>
                    <div className="text-xs text-[var(--text-muted)]">标题（可选）</div>
                    <input
                      value={docTitle}
                      onChange={(e) => setDocTitle(e.target.value)}
                      className="mt-1 w-full rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                      placeholder="留空则使用文件名"
                    />
                  </div>
                  <div>
                    <div className="text-xs text-[var(--text-muted)]">领域代码（可选）</div>
                    <input
                      value={docDomain}
                      onChange={(e) => setDocDomain(e.target.value)}
                      className="mt-1 w-full rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)]"
                      placeholder="例如：CAR-JOB"
                    />
                  </div>
                </div>

                {docAutoClassifyResult.length > 0 && (
                  <div className="rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] p-3">
                    <div className="mb-2 text-xs font-medium text-[var(--accent-primary)]">
                      🤖 AI自动分类建议
                    </div>
                    <div className="space-y-1">
                      {docAutoClassifyResult.map((result, idx) => (
                        <div key={result.domain} className="flex items-center gap-2 text-sm">
                          <span className="text-[var(--text-muted)]">#{idx + 1}</span>
                          <span className="font-mono text-xs">{result.domain}</span>
                          <div className="flex-1">
                            <div className="h-2 rounded-full bg-[var(--bg-tertiary)]">
                              <div
                                className="h-2 rounded-full bg-[var(--accent-primary)]"
                                style={{ width: `${result.confidence * 100}%` }}
                              />
                            </div>
                          </div>
                          <span className="text-xs text-[var(--text-muted)]">
                            {Math.round(result.confidence * 100)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <DomainSelector
                  selectedDomains={docSelectedDomains}
                  onChange={setDocSelectedDomains}
                  selectedTags={docSelectedTags}
                  onTagsChange={setDocSelectedTags}
                  enableAutoClassify={docEnableAutoClassify}
                  onAutoClassifyChange={setDocEnableAutoClassify}
                />
              </div>
            )}

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={onUpload}
                disabled={
                  loading ||
                  (tab === "csv" ? !csvFile : tab === "json" ? !jsonFile : !docFile)
                }
                className="rounded-md bg-[var(--accent-primary)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--accent-hover)] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? "导入中..." : "上传并导入"}
              </button>
              {uploadDisabledReason ? (
                <div className="text-xs text-[var(--text-muted)]">{uploadDisabledReason}</div>
              ) : null}
              <div className="text-xs text-[var(--text-muted)]">
                后端接口：
                {tab === "csv"
                  ? "POST /ingest/csv"
                  : tab === "json"
                    ? "POST /ingest/json"
                    : "POST /ingest/document"}
              </div>
            </div>

            {error ? (
              <div className="rounded-md border border-[color:var(--bg-tertiary)] bg-[rgba(239,68,68,0.08)] px-3 py-2 text-sm text-[var(--text-primary)]">
                <div className="font-medium">导入失败</div>
                <div className="mt-1 font-mono text-xs text-[var(--text-secondary)]">{error}</div>
              </div>
            ) : null}
          </div>
        </div>

        <div className="text-xs text-[var(--text-muted)]">
          导入完成后可前往「案例库 / 知识图谱」刷新查看。
        </div>
      </div>
    </AppShell>
  );
}
