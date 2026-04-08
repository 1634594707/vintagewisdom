"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import AppShell from "@/components/AppShell";
import DomainSelector from "@/components/DomainSelector";
import { EmptyState, NoticeBanner, SectionIntro, ToggleChip } from "@/components/ui/workspace";
import {
  api,
  type IngestCsvResponse,
  type IngestDocumentResponse,
  type IngestJsonResponse,
  type TaskStatusResponse,
} from "@/lib/api";
import { autoClassifyDomain } from "@/lib/domains";

type Tab = "csv" | "document" | "json";

export default function ImportPage() {
  const [tab, setTab] = useState<Tab>("csv");

  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvFileName, setCsvFileName] = useState("");
  const [csvDefaultDomain, setCsvDefaultDomain] = useState("");
  const [csvConflict, setCsvConflict] = useState<"skip" | "replace">("skip");
  const [csvEnableAutoClassify, setCsvEnableAutoClassify] = useState(true);
  const [csvSelectedDomains, setCsvSelectedDomains] = useState<string[]>([]);
  const [csvSelectedTags, setCsvSelectedTags] = useState<string[]>([]);

  const [docFile, setDocFile] = useState<File | null>(null);
  const [docFileName, setDocFileName] = useState("");
  const [docType, setDocType] = useState<"auto" | "pdf" | "docx">("auto");
  const [docCaseId, setDocCaseId] = useState("");
  const [docDomain, setDocDomain] = useState("");
  const [docTitle, setDocTitle] = useState("");
  const [docEnableAutoClassify, setDocEnableAutoClassify] = useState(true);
  const [docSelectedDomains, setDocSelectedDomains] = useState<string[]>([]);
  const [docSelectedTags, setDocSelectedTags] = useState<string[]>([]);
  const [docAutoClassifyResult, setDocAutoClassifyResult] = useState<Array<{ domain: string; confidence: number }>>([]);

  const [jsonFile, setJsonFile] = useState<File | null>(null);
  const [jsonFileName, setJsonFileName] = useState("");
  const [jsonDefaultDomain, setJsonDefaultDomain] = useState("");
  const [jsonEnableAutoClassify, setJsonEnableAutoClassify] = useState(true);
  const [jsonEnableAutoCluster, setJsonEnableAutoCluster] = useState(true);
  const [jsonSelectedDomains, setJsonSelectedDomains] = useState<string[]>([]);
  const [jsonSelectedTags, setJsonSelectedTags] = useState<string[]>([]);

  const [asyncTaskId, setAsyncTaskId] = useState("");
  const [taskStatus, setTaskStatus] = useState<TaskStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState("");
  const [csvResult, setCsvResult] = useState<IngestCsvResponse | null>(null);
  const [docResult, setDocResult] = useState<IngestDocumentResponse | null>(null);
  const [jsonResult, setJsonResult] = useState<IngestJsonResponse | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  const selectedFileName = useMemo(() => {
    if (tab === "csv") return csvFileName;
    if (tab === "json") return jsonFileName;
    return docFileName;
  }, [csvFileName, docFileName, jsonFileName, tab]);

  const accept = useMemo(() => {
    if (tab === "csv") return ".csv,text/csv";
    if (tab === "json") return ".json,application/json";
    return ".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document";
  }, [tab]);

  const activeResult = csvResult || jsonResult || docResult;
  const isAsyncProcessing =
    tab === "json" &&
    Boolean(asyncTaskId) &&
    Boolean(taskStatus) &&
    taskStatus?.status !== "completed" &&
    taskStatus?.status !== "failed";

  const uploadDisabledReason = useMemo(() => {
    if (importing) return "导入任务正在进行中。";
    if (tab === "csv" && !csvFile) return "请先选择 CSV 文件。";
    if (tab === "json" && !jsonFile) return "请先选择 JSON 文件。";
    if (tab === "document" && !docFile) return "请先选择 PDF 或 DOCX 文件。";
    return "";
  }, [csvFile, docFile, importing, jsonFile, tab]);

  const clearPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  const resetResults = () => {
    setCsvResult(null);
    setDocResult(null);
    setJsonResult(null);
  };

  const startTaskPolling = (taskId: string) => {
    clearPolling();
    pollingRef.current = setInterval(async () => {
      try {
        const status = await api.getTaskStatus(taskId);
        setTaskStatus(status);

        if (status.status === "completed" || status.status === "failed") {
          clearPolling();
          setLoading(false);
          setImporting(false);
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
    }, 1000);
  };

  const handleDocFileChange = async (file: File | null) => {
    setDocFile(file);
    setDocFileName(file?.name || "");
    setDocAutoClassifyResult([]);

    if (file && docEnableAutoClassify) {
      try {
        const text = await file.text();
        const preview = text.slice(0, 1000);
        const results = autoClassifyDomain(preview);
        setDocAutoClassifyResult(results);
        if (results.length > 0 && results[0].confidence > 0.5) setDocSelectedDomains([results[0].domain]);
      } catch {
        setDocAutoClassifyResult([]);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    if (tab === "csv") {
      setCsvFile(file);
      setCsvFileName(file?.name || "");
      return;
    }
    if (tab === "json") {
      setJsonFile(file);
      setJsonFileName(file?.name || "");
      return;
    }
    void handleDocFileChange(file);
  };

  async function onUpload() {
    setError("");
    resetResults();
    setImporting(true);
    setLoading(true);

    try {
      if (tab === "csv") {
        if (!csvFile) return;
        const response = await api.ingestCsv(csvFile, {
          default_domain: csvDefaultDomain || undefined,
          on_conflict: csvConflict,
          auto_classify: csvEnableAutoClassify,
          domains: csvSelectedDomains.length > 0 ? csvSelectedDomains : undefined,
          tags: csvSelectedTags.length > 0 ? csvSelectedTags : undefined,
        });
        setCsvResult(response);
        setImporting(false);
        setLoading(false);
        return;
      }

      if (tab === "json") {
        if (!jsonFile) return;
        const response = await api.ingestJsonAsync(jsonFile, {
          default_domain: jsonDefaultDomain || undefined,
          auto_classify: jsonEnableAutoClassify,
          auto_cluster: jsonEnableAutoCluster,
          domains: jsonSelectedDomains.length > 0 ? jsonSelectedDomains : undefined,
          tags: jsonSelectedTags.length > 0 ? jsonSelectedTags : undefined,
        });
        setAsyncTaskId(response.task_id);
        setTaskStatus(null);
        startTaskPolling(response.task_id);
        return;
      }

      if (!docFile) return;
      const response = await api.ingestDocument(docFile, {
        doc_type: docType,
        case_id: docCaseId || undefined,
        domain: docDomain || (docSelectedDomains.length > 0 ? docSelectedDomains[0] : undefined),
        title: docTitle || undefined,
        auto_classify: docEnableAutoClassify,
        domains: docSelectedDomains.length > 0 ? docSelectedDomains : undefined,
        tags: docSelectedTags.length > 0 ? docSelectedTags : undefined,
      });
      setDocResult(response);
      setImporting(false);
      setLoading(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setLoading(false);
      setImporting(false);
      clearPolling();
    }
  }

  function onClear() {
    clearPolling();
    setAsyncTaskId("");
    setTaskStatus(null);
    setLoading(false);
    setImporting(false);
    setError("");
    resetResults();

    setCsvFile(null);
    setCsvFileName("");
    setCsvDefaultDomain("");
    setCsvConflict("skip");
    setCsvEnableAutoClassify(true);
    setCsvSelectedDomains([]);
    setCsvSelectedTags([]);

    setJsonFile(null);
    setJsonFileName("");
    setJsonDefaultDomain("");
    setJsonEnableAutoClassify(true);
    setJsonEnableAutoCluster(true);
    setJsonSelectedDomains([]);
    setJsonSelectedTags([]);

    setDocFile(null);
    setDocFileName("");
    setDocType("auto");
    setDocCaseId("");
    setDocDomain("");
    setDocTitle("");
    setDocEnableAutoClassify(true);
    setDocSelectedDomains([]);
    setDocSelectedTags([]);
    setDocAutoClassifyResult([]);

    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  if (importing || isAsyncProcessing) {
    const progress = Math.max(0, Math.min(100, taskStatus?.overall_percent ?? taskStatus?.progress_percent ?? 0));

    return (
      <AppShell title="导入中心">
        <div className="flex min-h-[70dvh] items-center justify-center">
          <div className="vw-panel w-full max-w-3xl rounded-[28px] p-6 md:p-8">
            <div className="flex flex-col items-center text-center">
              <div className="h-20 w-20 animate-spin rounded-full border-4 border-[rgba(0,0,0,0.08)] border-t-[var(--accent-primary)]" />
              <h2 className="vw-title mt-6 text-[42px] font-semibold">{tab === "json" ? "后台导入处理中" : "正在整理导入材料"}</h2>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--text-muted)]">
                {selectedFileName ? `当前文件：${selectedFileName}` : "系统正在处理你上传的文件，请稍候。"}
              </p>
            </div>

            <div className="mt-8 rounded-xl border border-[color:var(--border-subtle)] bg-[#f8f9fa] p-5">
              <div className="flex items-center justify-between text-sm">
                <span className="text-[var(--text-secondary)]">整体进度</span>
                <span className="vw-mono text-[var(--text-primary)]">{progress}%</span>
              </div>
              <div className="mt-3 h-3 rounded-full bg-[rgba(0,0,0,0.08)]">
                <div className="h-3 rounded-full bg-gradient-to-r from-[var(--accent-primary)] to-[var(--accent-secondary)]" style={{ width: `${progress}%` }} />
              </div>
            </div>

            {taskStatus ? (
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <ProcessCard label="任务编号" value={asyncTaskId || "-"} mono />
                <ProcessCard label="任务状态" value={translateTaskStatus(taskStatus.status)} />
                <ProcessCard label="当前阶段" value={translateStage(taskStatus.stage)} />
                <ProcessCard label="当前处理对象" value={taskStatus.current_action || taskStatus.current_case || "-"} />
              </div>
            ) : null}
          </div>
        </div>
      </AppShell>
    );
  }

  if (activeResult) {
    const resultTitle = csvResult ? "CSV 导入完成" : jsonResult ? "JSON 导入完成" : "文档导入完成";

    return (
      <AppShell title="导入中心">
        <div className="space-y-4">
          <SectionIntro
            eyebrow="导入结果"
            title={resultTitle}
            description="文件已经处理完成，你可以继续导入下一批材料，或者回到案例库查看实际入库结果。"
            actions={
              <div className="flex flex-wrap gap-2">
                <button type="button" onClick={resetResults} className="vw-btn-secondary px-4 py-2 text-sm">
                  继续导入
                </button>
                <button type="button" onClick={onClear} className="vw-btn-primary px-4 py-2 text-sm font-medium">
                  清空全部
                </button>
              </div>
            }
          />

          <section className="vw-card rounded-xl p-5">
            <div className="vw-eyebrow">原始结果</div>
            <pre className="vw-scrollbar mt-4 max-h-[520px] overflow-auto rounded-xl border border-[color:var(--border-subtle)] bg-[#f8f9fa] p-4 text-sm leading-6 text-[var(--text-secondary)]">
              {JSON.stringify(activeResult, null, 2)}
            </pre>
          </section>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell title="导入中心">
      <div className="space-y-4">
        <SectionIntro
          eyebrow="材料入库台"
          title="把案例与材料整理进知识底座"
          description="支持 CSV、JSON、PDF 与 Word。你可以指定默认领域、补充标签，并在导入时启用 AI 自动分类。"
          actions={
            <div className="flex flex-wrap gap-2">
              <ToggleChip active={tab === "csv"} onClick={() => setTab("csv")} label="CSV 批量导入" />
              <ToggleChip active={tab === "document"} onClick={() => setTab("document")} label="PDF / Word 文档" />
              <ToggleChip active={tab === "json"} onClick={() => setTab("json")} label="JSON 异步导入" />
            </div>
          }
        />

        {error ? <NoticeBanner tone="error">导入失败：{error}</NoticeBanner> : null}

        <section className="grid gap-4 xl:grid-cols-[1fr_0.86fr]">
          <div className="vw-card rounded-[24px] p-5">
            <div className="vw-eyebrow">文件与参数</div>
            <h3 className="vw-title mt-1 text-[34px] font-semibold">上传材料</h3>

            <div className="mt-5 space-y-5">
              <div className="rounded-xl border border-dashed border-[color:var(--border-strong)] bg-[#f8f9fa] p-5">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={accept}
                  onChange={handleFileChange}
                  className="block w-full text-sm text-[var(--text-secondary)] file:mr-4 file:rounded-full file:border-0 file:bg-[var(--accent-primary)] file:px-4 file:py-2 file:text-sm file:font-medium file:text-white file:cursor-pointer hover:file:bg-[var(--accent-hover)]"
                />
                <div className="mt-3 text-sm text-[var(--text-muted)]">
                  当前文件：<span className="text-[var(--text-secondary)]">{selectedFileName || "尚未选择"}</span>
                </div>
              </div>

              {tab === "csv" ? (
                <div className="grid gap-4 md:grid-cols-2">
                  <Field label="默认领域代码">
                    <input value={csvDefaultDomain} onChange={(e) => setCsvDefaultDomain(e.target.value)} placeholder="例如 TEC-REF / CAR-NEG" className="vw-input h-11 rounded-2xl px-4 text-sm" />
                  </Field>
                  <Field label="冲突策略">
                    <select value={csvConflict} onChange={(e) => setCsvConflict(e.target.value as "skip" | "replace")} className="vw-select h-11 rounded-2xl px-4 text-sm">
                      <option value="skip">跳过已存在</option>
                      <option value="replace">覆盖旧记录</option>
                    </select>
                  </Field>
                </div>
              ) : null}

              {tab === "json" ? (
                <div className="grid gap-4 md:grid-cols-2">
                  <Field label="默认领域代码">
                    <input value={jsonDefaultDomain} onChange={(e) => setJsonDefaultDomain(e.target.value)} placeholder="例如 HIS-POL" className="vw-input h-11 rounded-2xl px-4 text-sm" />
                  </Field>
                  <label className="flex items-center gap-3 rounded-[24px] border border-[color:var(--border-subtle)] bg-[#f8f9fa] px-4 py-4">
                    <input type="checkbox" checked={jsonEnableAutoCluster} onChange={(e) => setJsonEnableAutoCluster(e.target.checked)} className="h-4 w-4 rounded border-[color:var(--border-subtle)] bg-transparent" />
                    <div>
                      <div className="text-sm font-medium text-[var(--text-primary)]">启用自动聚类</div>
                      <div className="mt-1 text-xs text-[var(--text-muted)]">异步导入后尝试把相似案例自动归组。</div>
                    </div>
                  </label>
                </div>
              ) : null}

              {tab === "document" ? (
                <div className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <Field label="文档类型">
                      <select value={docType} onChange={(e) => setDocType(e.target.value as "auto" | "pdf" | "docx")} className="vw-select h-11 rounded-2xl px-4 text-sm">
                        <option value="auto">自动识别</option>
                        <option value="pdf">PDF</option>
                        <option value="docx">DOCX</option>
                      </select>
                    </Field>
                    <Field label="案例编号">
                      <input value={docCaseId} onChange={(e) => setDocCaseId(e.target.value)} placeholder="留空则自动生成" className="vw-input h-11 rounded-2xl px-4 text-sm" />
                    </Field>
                    <Field label="标题">
                      <input value={docTitle} onChange={(e) => setDocTitle(e.target.value)} placeholder="留空则使用文件名" className="vw-input h-11 rounded-2xl px-4 text-sm" />
                    </Field>
                    <Field label="领域代码">
                      <input value={docDomain} onChange={(e) => setDocDomain(e.target.value)} placeholder="例如 TEC-AI" className="vw-input h-11 rounded-2xl px-4 text-sm" />
                    </Field>
                  </div>

                  {docAutoClassifyResult.length > 0 ? (
                    <div className="rounded-[24px] border border-[color:var(--border-subtle)] bg-[#f8f9fa] p-4">
                      <div className="text-sm font-medium text-[var(--text-primary)]">AI 分类建议</div>
                      <div className="mt-4 space-y-3">
                        {docAutoClassifyResult.map((item) => (
                          <div key={item.domain}>
                            <div className="mb-1 flex items-center justify-between text-sm">
                              <span className="vw-mono text-[var(--text-secondary)]">{item.domain}</span>
                              <span className="text-[var(--text-muted)]">{Math.round(item.confidence * 100)}%</span>
                            </div>
                            <div className="h-2.5 rounded-full bg-[rgba(0,0,0,0.08)]">
                              <div className="h-2.5 rounded-full bg-gradient-to-r from-[var(--accent-primary)] to-[var(--accent-secondary)]" style={{ width: `${item.confidence * 100}%` }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}

              <DomainSelector
                selectedDomains={tab === "csv" ? csvSelectedDomains : tab === "json" ? jsonSelectedDomains : docSelectedDomains}
                onChange={tab === "csv" ? setCsvSelectedDomains : tab === "json" ? setJsonSelectedDomains : setDocSelectedDomains}
                selectedTags={tab === "csv" ? csvSelectedTags : tab === "json" ? jsonSelectedTags : docSelectedTags}
                onTagsChange={tab === "csv" ? setCsvSelectedTags : tab === "json" ? setJsonSelectedTags : setDocSelectedTags}
                enableAutoClassify={tab === "csv" ? csvEnableAutoClassify : tab === "json" ? jsonEnableAutoClassify : docEnableAutoClassify}
                onAutoClassifyChange={tab === "csv" ? setCsvEnableAutoClassify : tab === "json" ? setJsonEnableAutoClassify : setDocEnableAutoClassify}
              />
            </div>
          </div>

          <div className="space-y-4">
            <div className="vw-card rounded-[24px] p-5">
              <div className="vw-eyebrow">执行面板</div>
              <h3 className="vw-title mt-1 text-[34px] font-semibold">开始入库</h3>
              <div className="mt-5 space-y-3">
                <button type="button" onClick={onUpload} disabled={loading || !selectedFileName} className="vw-btn-primary w-full px-5 py-3 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-60">
                  {loading ? "导入中..." : "上传并导入"}
                </button>
                <button type="button" onClick={onClear} className="vw-btn-secondary w-full px-5 py-3 text-sm">
                  清空当前状态
                </button>
                <div className="rounded-[20px] border border-[color:var(--border-subtle)] bg-[#f8f9fa] p-4 text-sm text-[var(--text-muted)]">
                  {uploadDisabledReason || "文件与参数已经就绪，可以开始导入。"}
                </div>
              </div>
            </div>

            <div className="vw-card rounded-[24px] p-5">
              <div className="vw-eyebrow">接口路径</div>
              <h3 className="vw-title mt-1 text-[34px] font-semibold">当前端点</h3>
              <div className="vw-mono mt-4 rounded-[20px] border border-[color:var(--border-subtle)] bg-[#f8f9fa] p-4 text-sm text-[var(--text-secondary)]">
                {tab === "csv" ? "POST /ingest/csv" : tab === "json" ? "POST /ingest/json/async" : "POST /ingest/document"}
              </div>
            </div>

            {!selectedFileName ? <EmptyState title="还没有选中文件" hint="先选择一份要导入的材料，再设置领域与标签。" /> : null}
          </div>
        </section>
      </div>
    </AppShell>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <div className="mb-2 text-sm font-medium text-[var(--text-primary)]">{label}</div>
      {children}
    </label>
  );
}

function ProcessCard({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="rounded-[24px] border border-[color:var(--border-subtle)] bg-[#f8f9fa] p-4">
      <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--text-disabled)]">{label}</div>
      <div className={mono ? "vw-mono mt-2 text-sm text-[var(--text-secondary)]" : "mt-2 text-sm text-[var(--text-secondary)]"}>{value}</div>
    </div>
  );
}

function translateTaskStatus(status?: TaskStatusResponse["status"]) {
  if (status === "pending") return "等待中";
  if (status === "processing") return "处理中";
  if (status === "completed") return "已完成";
  if (status === "failed") return "失败";
  return "-";
}

function translateStage(stage?: string) {
  if (stage === "import") return "导入";
  if (stage === "classify") return "AI 分类";
  if (stage === "kg_extract") return "知识图谱抽取";
  return stage || "-";
}
