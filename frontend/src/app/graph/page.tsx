"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import AppShell from "@/components/AppShell";
import { NoticeBanner, SectionIntro, ToggleChip } from "@/components/ui/workspace";
import GraphViewSigma from "@/components/GraphViewSigma";
import { api, type GraphResponse } from "@/lib/api";

const RELATION_OPTIONS = ["related_to", "causes", "leads_to", "part_of", "used_for"];

export default function GraphPage() {
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [mode, setMode] = useState<"case" | "kg">("case");
  const [kgQuery, setKgQuery] = useState("");
  const [kgSeed, setKgSeed] = useState("");
  const [kgRelationType, setKgRelationType] = useState("");
  const [useAIClustering, setUseAIClustering] = useState(false);
  const [showSimilarEdges, setShowSimilarEdges] = useState(true);

  const graphPath = useMemo(() => {
    if (mode === "kg") {
      const q = kgQuery.trim();
      const seed = kgSeed.trim();
      const relationType = kgRelationType.trim();
      const relationPart = relationType ? `&relation_type=${encodeURIComponent(relationType)}` : "";
      if (seed) return `/graph?view=kg&depth=2${relationPart}&seed_entity_id=${encodeURIComponent(seed)}`;
      return q ? `/graph?view=kg&depth=2${relationPart}&q=${encodeURIComponent(q)}` : `/graph?view=kg&depth=2${relationPart}`;
    }
    
    // 案例图谱：可选的AI功能
    const params = new URLSearchParams();
    if (useAIClustering) {
      params.append("use_ai_clustering", "true");
    }
    if (showSimilarEdges) {
      params.append("similarity_threshold", "0.4");
      params.append("max_similar_edges", "60");
      params.append("max_cases_for_similarity", "100"); // 限制计算数量以提高速度
    } else {
      params.append("max_similar_edges", "0"); // 不计算相似边
    }
    
    return `/graph?${params.toString()}`;
  }, [kgQuery, kgRelationType, kgSeed, mode, useAIClustering, showSimilarEdges]);

  const fetchGraph = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.graph(graphPath);
      setGraph(data);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [graphPath]);

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  const graphStats = graph?.stats;

  return (
    <AppShell title="知识图谱" variant="canvas">
      <div className="space-y-4">
        <SectionIntro
          eyebrow="关系画布"
          title="案例关系与知识链路"
          description="从图谱视角查看案例、实体、聚类与关系链，理解结构而不是只读条目。"
          actions={
            <div className="grid gap-3 sm:grid-cols-4">
              <StatChip label="节点" value={graph?.nodes.length ?? 0} />
              <StatChip label="边" value={graph?.edges.length ?? 0} />
              <StatChip label="领域" value={graphStats?.domain_count ?? 0} />
              <StatChip label="案例" value={graphStats?.case_count ?? 0} />
            </div>
          }
          aside={
            <div className="flex flex-col gap-3 xl:flex-row xl:items-center">
              <div className="flex flex-wrap gap-2">
                <ToggleChip active={mode === "case"} onClick={() => setMode("case")} label="案例图谱" />
                <ToggleChip active={mode === "kg"} onClick={() => setMode("kg")} label="知识图谱" />
              </div>
              <div className="flex flex-col gap-2 xl:flex-row">
                {mode === "kg" ? (
                  <>
                    <select 
                      value={kgRelationType} 
                      onChange={(e) => { setKgSeed(""); setKgRelationType(e.target.value); }} 
                      className="vw-input h-11 rounded-2xl px-4 text-sm"
                    >
                      <option value="">全部关系</option>
                      {RELATION_OPTIONS.map((option) => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                    <input 
                      value={kgQuery} 
                      onChange={(e) => { setKgSeed(""); setKgQuery(e.target.value); }} 
                      placeholder="搜索实体或聚类" 
                      className="vw-input h-11 min-w-[260px] rounded-2xl px-4 text-sm" 
                    />
                  </>
                ) : (
                  <div className="flex gap-2">
                    <button
                      onClick={() => setShowSimilarEdges(!showSimilarEdges)}
                      className={`px-4 py-2 text-sm rounded-xl border ${
                        showSimilarEdges 
                          ? "border-[color:var(--accent-primary)] bg-[var(--accent-light)] text-[var(--accent-primary)]"
                          : "border-[color:var(--border-subtle)] bg-white text-[var(--text-secondary)]"
                      }`}
                    >
                      相似关系
                    </button>
                    <button
                      onClick={() => setUseAIClustering(!useAIClustering)}
                      className={`px-4 py-2 text-sm rounded-xl border ${
                        useAIClustering 
                          ? "border-[color:var(--accent-primary)] bg-[var(--accent-light)] text-[var(--accent-primary)]"
                          : "border-[color:var(--border-subtle)] bg-white text-[var(--text-secondary)]"
                      }`}
                    >
                      AI聚类
                    </button>
                  </div>
                )}
                <button 
                  type="button" 
                  onClick={fetchGraph} 
                  disabled={loading} 
                  className="vw-btn-primary px-5 py-2.5 text-sm font-medium disabled:opacity-60"
                >
                  {loading ? "刷新中..." : "刷新图谱"}
                </button>
              </div>
            </div>
          }
        />

        {error ? <NoticeBanner tone="error">图谱加载失败：{error}</NoticeBanner> : null}

        <section className="relative overflow-hidden rounded-[28px] border border-[color:var(--border-subtle)] bg-gradient-to-b from-white to-[#f8fafc] shadow-[0_8px_24px_rgba(15,23,42,0.06)]">
          <div className="absolute left-4 top-4 z-20 flex flex-wrap gap-2">
            <OverlayBadge label={mode === "case" ? "案例图谱" : "知识图谱"} />
            {mode === "case" && showSimilarEdges && graphStats && graphStats.similar_edge_count > 0 ? (
              <OverlayBadge label={`${graphStats.similar_edge_count} 条相似关系`} />
            ) : null}
            {mode === "case" && useAIClustering && graphStats && graphStats.cluster_count > 0 ? (
              <OverlayBadge label={`${graphStats.cluster_count} 个AI聚类`} />
            ) : null}
          </div>

          <div className="h-[calc(100dvh-220px)] min-h-[640px] lg:min-h-[720px]">
            {graph ? (
              <GraphViewSigma
                graph={graph}
                isKg={mode === "kg"}
                onExpandSeed={(entityId) => {
                  setKgQuery("");
                  setKgSeed(entityId);
                }}
              />
            ) : (
              <div className="flex h-full items-center justify-center text-[var(--text-muted)]">
                {loading ? "正在加载图谱..." : "当前没有可显示的图谱数据"}
              </div>
            )}
          </div>
        </section>
        
        {/* 图例说明 */}
        <div className="rounded-2xl border border-[color:var(--border-subtle)] bg-[#f8f9fa] p-4">
          <div className="text-sm font-medium text-[var(--text-primary)] mb-3">图例说明</div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span className="text-[var(--text-secondary)]">领域节点</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-[var(--text-secondary)]">案例节点</span>
            </div>
            {useAIClustering && (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                <span className="text-[var(--text-secondary)]">聚类节点</span>
              </div>
            )}
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-gray-400"></div>
              <span className="text-[var(--text-secondary)]">实体节点</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-[2px] w-5 rounded bg-orange-500"></div>
              <span className="text-[var(--text-secondary)]">相似关系边</span>
            </div>
          </div>
          <div className="mt-3 pt-3 border-t border-[color:var(--border-subtle)] text-xs text-[var(--text-muted)]">
            提示：点击节点查看详情，拖拽节点调整布局，滚轮缩放视图。启用&quot;相似关系&quot;和&quot;AI聚类&quot;会增加计算时间。
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function StatChip({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-2xl border border-[color:var(--border-subtle)] bg-[#f8f9fa] px-4 py-3">
      <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--text-disabled)]">{label}</div>
      <div className="mt-1 text-lg font-medium text-[var(--text-primary)]">{value}</div>
    </div>
  );
}

function OverlayBadge({ label }: { label: string }) {
  return (
    <div className="rounded-full border border-[color:var(--border-subtle)] bg-white/90 px-3 py-1.5 text-xs text-[var(--text-secondary)] backdrop-blur">
      {label}
    </div>
  );
}
