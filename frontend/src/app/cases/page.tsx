"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import AppShell from "@/components/AppShell";
import { EmptyState, MetricCard, NoticeBanner, SectionIntro } from "@/components/ui/workspace";
import { api, apiExtended, FALLBACK_CASES, isFetchFailure, type Case } from "@/lib/api";

export default function CasesPage() {
  return (
    <Suspense fallback={<CasesPageFallback />}>
      <CasesPageContent />
    </Suspense>
  );
}

function CasesPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const q = searchParams.get("q") || "";
  const domain = searchParams.get("domain") || "";
  const confidence = searchParams.get("confidence") || "";
  
  const [cases, setCases] = useState<Case[]>([]);
  const [degraded, setDegraded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selectedCases, setSelectedCases] = useState<Set<string>>(new Set());
  const [showBatchActions, setShowBatchActions] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const casesData = await api.cases();
      setCases(casesData.length > 0 ? casesData : FALLBACK_CASES);
      setDegraded(casesData.length === 0);
    } catch (error) {
      if (isFetchFailure(error)) {
        setCases(FALLBACK_CASES);
        setDegraded(true);
      }
    } finally {
      setLoading(false);
    }
  };

  const filtered = cases.filter((c) => {
    if (q && !(
      c.id.toLowerCase().includes(q.toLowerCase()) ||
      c.title.toLowerCase().includes(q.toLowerCase()) ||
      (c.domain || "").toLowerCase().includes(q.toLowerCase()) ||
      (c.lesson_core || "").toLowerCase().includes(q.toLowerCase())
    )) {
      return false;
    }
    if (domain && c.domain !== domain) {
      return false;
    }
    if (confidence && c.confidence !== confidence) {
      return false;
    }
    return true;
  });

  const activeDomains = [...new Set(cases.map((item) => item.domain).filter(Boolean))].slice(0, 6);

  const toggleCaseSelection = (caseId: string) => {
    const newSelected = new Set(selectedCases);
    if (newSelected.has(caseId)) {
      newSelected.delete(caseId);
    } else {
      newSelected.add(caseId);
    }
    setSelectedCases(newSelected);
    setShowBatchActions(newSelected.size > 0);
  };

  const selectAll = () => {
    setSelectedCases(new Set(filtered.map(c => c.id)));
    setShowBatchActions(true);
  };

  const clearSelection = () => {
    setSelectedCases(new Set());
    setShowBatchActions(false);
  };

  const handleBatchDelete = async () => {
    if (!confirm(`确定要删除选中的 ${selectedCases.size} 个案例吗？`)) {
      return;
    }
    try {
      await apiExtended.batchDeleteCases(Array.from(selectedCases));
      await loadData();
      clearSelection();
    } catch (err) {
      alert("批量删除失败: " + (err instanceof Error ? err.message : "未知错误"));
    }
  };

  const handleBatchExport = async () => {
    try {
      const result = await apiExtended.batchExportCases(Array.from(selectedCases), "json");
      const blob = new Blob([JSON.stringify(result.data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `cases_export_${new Date().toISOString().split("T")[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      alert("批量导出失败: " + (err instanceof Error ? err.message : "未知错误"));
    }
  };

  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const query = formData.get("q") as string;
    const params = new URLSearchParams();
    if (query) params.set("q", query);
    if (domain) params.set("domain", domain);
    if (confidence) params.set("confidence", confidence);
    router.push(`/cases?${params.toString()}`);
  };

  if (loading) {
    return (
      <AppShell title="案例库">
        <div className="flex items-center justify-center py-12">
          <div className="text-lg text-[var(--text-muted)]">加载中...</div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell title="案例库">
      <div className="space-y-4">
        <SectionIntro
          eyebrow="案例档案库"
          title="像查阅馆藏一样浏览历史案例"
          description="你可以按标题、领域、经验教训和案例编号检索，把案例库当作一套可快速翻阅的判断档案，而不是单纯的列表页。"
          actions={
            <form className="flex w-full max-w-xl flex-col gap-2 sm:flex-row" onSubmit={handleSearch}>
              <input
                name="q"
                defaultValue={q}
                placeholder="搜索编号、标题、领域或经验教训"
                className="vw-input h-11 rounded-2xl px-4 text-sm"
              />
              <button type="submit" className="vw-btn-primary px-5 py-2.5 text-sm font-medium">
                开始检索
              </button>
            </form>
          }
          aside={
            <div className="flex flex-wrap gap-2">
              <Link href="/cases" className={`vw-badge ${!q && !domain && !confidence ? "vw-badge-accent" : ""}`}>
                全部
              </Link>
              {activeDomains.map((dom) => (
                <Link 
                  key={dom} 
                  href={`/cases?domain=${encodeURIComponent(dom || "")}`} 
                  className={`vw-badge ${domain === dom ? "vw-badge-accent" : ""}`}
                >
                  {dom}
                </Link>
              ))}
              <Link href="/export" className="vw-badge vw-badge-success">
                导出数据
              </Link>
            </div>
          }
        />

        {degraded && (
          <NoticeBanner tone="warning">
            当前无法读取后端实时数据，案例库正在展示示例数据，以保证前端仍可继续浏览。
          </NoticeBanner>
        )}

        {showBatchActions && (
          <div className="vw-card rounded-[24px] p-4 flex items-center justify-between">
            <div className="text-sm text-[var(--text-primary)]">
              已选择 {selectedCases.size} 个案例
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleBatchExport}
                className="vw-btn-secondary px-4 py-2 text-sm"
              >
                导出选中
              </button>
              <button
                onClick={handleBatchDelete}
                className="vw-btn-secondary px-4 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                删除选中
              </button>
              <button
                onClick={clearSelection}
                className="vw-btn-secondary px-4 py-2 text-sm"
              >
                取消选择
              </button>
            </div>
          </div>
        )}

        <section className="grid gap-4 md:grid-cols-3">
          <MetricCard label="检索结果" value={filtered.length} hint={q || domain || confidence ? "已应用筛选" : "当前展示完整案例库"} />
          <MetricCard label="案例总量" value={cases.length} hint="当前已入库案例数" />
          <MetricCard label="已选择" value={selectedCases.size} hint="批量操作模式" />
        </section>

        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            <button
              onClick={selectAll}
              className="vw-btn-secondary px-4 py-2 text-sm"
            >
              全选
            </button>
            {selectedCases.size > 0 && (
              <button
                onClick={clearSelection}
                className="vw-btn-secondary px-4 py-2 text-sm"
              >
                清除选择
              </button>
            )}
          </div>
          
          <div className="flex gap-2">
            <select
              value={confidence}
              onChange={(e) => {
                const params = new URLSearchParams(searchParams.toString());
                if (e.target.value) {
                  params.set("confidence", e.target.value);
                } else {
                  params.delete("confidence");
                }
                router.push(`/cases?${params.toString()}`);
              }}
              className="vw-input h-10 rounded-xl px-3 text-sm"
            >
              <option value="">所有置信度</option>
              <option value="high">高</option>
              <option value="medium">中</option>
              <option value="low">低</option>
            </select>
          </div>
        </div>

        <section className="space-y-3">
          {filtered.length > 0 ? (
            filtered.map((item) => (
              <div
                key={item.id}
                className={`vw-card rounded-[24px] p-5 hover:border-[color:var(--accent-glow)] hover:-translate-y-0.5 ${
                  selectedCases.has(item.id) ? "border-[color:var(--accent-primary)] bg-[var(--accent-light)]" : ""
                }`}
              >
                <div className="flex items-start gap-4">
                  <input
                    type="checkbox"
                    checked={selectedCases.has(item.id)}
                    onChange={() => toggleCaseSelection(item.id)}
                    className="mt-1 h-5 w-5 rounded border-gray-300"
                  />
                  
                  <Link
                    href={`/cases/${encodeURIComponent(item.id)}`}
                    className="flex-1 block"
                  >
                    <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="vw-badge vw-badge-accent">{item.domain || "未分类"}</span>
                          <span className="vw-mono text-[11px] text-[var(--text-disabled)]">{item.id}</span>
                        </div>
                        <div className="mt-3 text-lg font-medium text-[var(--text-primary)]">{item.title}</div>
                        <div className="mt-2 line-clamp-2 max-w-4xl text-sm leading-6 text-[var(--text-muted)]">
                          {item.lesson_core || item.description || "这个案例暂时还没有总结出核心经验。"}
                        </div>
                      </div>

                      <div className="grid shrink-0 gap-3 sm:grid-cols-3 xl:w-[340px] xl:grid-cols-1">
                        <InfoPill label="最近更新" value={item.updated_at || "-"} />
                        <InfoPill label="置信度" value={item.confidence || "-"} />
                        <InfoPill label="结果时间窗" value={item.outcome_timeline || "-"} />
                      </div>
                    </div>
                  </Link>
                </div>
              </div>
            ))
          ) : (
            <EmptyState title="没有找到匹配案例" hint="试着放宽关键词，或者先去导入中心补充更多材料。" />
          )}
        </section>
      </div>
    </AppShell>
  );
}

function InfoPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[color:var(--border-subtle)] bg-[#f8f9fa] p-3">
      <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--text-disabled)]">{label}</div>
      <div className="mt-2 text-sm text-[var(--text-secondary)]">{value}</div>
    </div>
  );
}

function CasesPageFallback() {
  return (
    <AppShell title="案例库">
      <div className="flex items-center justify-center py-12">
        <div className="text-lg text-[var(--text-muted)]">加载中...</div>
      </div>
    </AppShell>
  );
}
