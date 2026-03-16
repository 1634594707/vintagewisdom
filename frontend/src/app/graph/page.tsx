"use client";

import { useEffect, useMemo, useState } from "react";
import AppShell from "@/components/AppShell";
import GraphViewSigma from "@/components/GraphViewSigma";
import { api, type GraphResponse } from "@/lib/api";

export default function GraphPage() {
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [mode, setMode] = useState<"case" | "kg">("case");
  const [kgQuery, setKgQuery] = useState<string>("");
  const [kgSeed, setKgSeed] = useState<string>("");
  const [kgRelationType, setKgRelationType] = useState<string>("");

  const graphPath = useMemo(() => {
    if (mode === "kg") {
      const q = kgQuery.trim();
      const seed = kgSeed.trim();
      const rt = kgRelationType.trim();
      const rtPart = rt ? `&relation_type=${encodeURIComponent(rt)}` : "";
      if (seed) return `/graph?view=kg&depth=2${rtPart}&seed_entity_id=${encodeURIComponent(seed)}`;
      return q ? `/graph?view=kg&depth=2${rtPart}&q=${encodeURIComponent(q)}` : `/graph?view=kg&depth=2${rtPart}`;
    }
    return "/graph";
  }, [kgQuery, kgSeed, kgRelationType, mode]);

  const fetchGraph = async () => {
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
  };

  useEffect(() => {
    fetchGraph();
  }, [graphPath]);

  return (
    <AppShell title="知识图谱" variant="canvas">
      <div className="relative h-[calc(100dvh-56px)] min-h-[700px] bg-[var(--bg-secondary)]">
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
          <div className="flex h-full items-center justify-center rounded-lg border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] text-[var(--text-muted)]">
            {loading ? "加载中..." : "暂无数据"}
          </div>
        )}

        {/* Floating toolbar - MIROFISH style */}
        <div className="pointer-events-none absolute left-3 right-3 top-3 z-40 flex items-start justify-between gap-3">
          <div className="pointer-events-auto rounded-lg border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)]/95 px-3 py-2 backdrop-blur-sm">
            <div className="text-xs text-[var(--text-secondary)]">
              {mode === "case" ? "Case Graph" : "Knowledge Graph"}
            </div>
            {error ? (
              <div className="mt-1 max-w-[520px] text-[11px] text-red-300">加载失败: {error}</div>
            ) : null}
          </div>

          <div className="pointer-events-auto flex flex-wrap items-center justify-end gap-2">
            <div className="flex items-center rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-0.5">
              <button
                type="button"
                onClick={() => setMode("case")}
                className={
                  mode === "case"
                    ? "rounded bg-[var(--accent-primary)] px-2 py-1 text-xs text-white"
                    : "rounded px-2 py-1 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                }
              >
                Case
              </button>
              <button
                type="button"
                onClick={() => setMode("kg")}
                className={
                  mode === "kg"
                    ? "rounded bg-[var(--accent-primary)] px-2 py-1 text-xs text-white"
                    : "rounded px-2 py-1 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                }
              >
                KG
              </button>
            </div>

            {mode === "kg" ? (
              <>
                <select
                  value={kgRelationType}
                  onChange={(e) => {
                    setKgSeed("");
                    setKgRelationType(e.target.value);
                  }}
                  className="h-8 rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] px-2 text-sm text-[var(--text-primary)] outline-none focus:border-[color:var(--accent-primary)]"
                >
                  <option value="">全部关系</option>
                  <option value="related_to">related_to</option>
                  <option value="causes">causes</option>
                  <option value="leads_to">leads_to</option>
                  <option value="part_of">part_of</option>
                  <option value="used_for">used_for</option>
                </select>
                <input
                  value={kgQuery}
                  onChange={(e) => {
                    setKgSeed("");
                    setKgQuery(e.target.value);
                  }}
                  placeholder="搜索实体..."
                  className="h-8 w-56 rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] px-3 text-sm text-[var(--text-primary)] outline-none focus:border-[color:var(--accent-primary)]"
                />
              </>
            ) : null}

            <button
              type="button"
              onClick={fetchGraph}
              disabled={loading}
              className="h-8 rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] px-3 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] disabled:opacity-50"
            >
              {loading ? "刷新中..." : "刷新"}
            </button>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
