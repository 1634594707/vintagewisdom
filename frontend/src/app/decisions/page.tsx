"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import { apiExtended, type DecisionLog } from "@/lib/api";

export default function DecisionsPage() {
  const [loading, setLoading] = useState(true);
  const [decisions, setDecisions] = useState<DecisionLog[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDecisions();
  }, []);

  const loadDecisions = async () => {
    try {
      const data = await apiExtended.listDecisions(100);
      setDecisions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      loadDecisions();
      return;
    }

    setLoading(true);
    try {
      const data = await apiExtended.searchDecisions(searchQuery);
      setDecisions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "搜索失败");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("确定要删除这条决策记录吗？")) {
      return;
    }

    try {
      await apiExtended.deleteDecision(id);
      setDecisions(decisions.filter((d) => d.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    }
  };

  if (loading) {
    return (
      <AppShell title="决策历史">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="text-lg text-[var(--text-muted)]">加载中...</div>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell title="决策历史">
      <div className="space-y-4">
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索决策内容..."
            className="vw-input flex-1 h-11 rounded-2xl px-4 text-sm"
          />
          <button type="submit" className="vw-btn-primary px-5 py-2.5 text-sm font-medium">
            搜索
          </button>
          {searchQuery && (
            <button
              type="button"
              onClick={() => {
                setSearchQuery("");
                loadDecisions();
              }}
              className="vw-btn-secondary px-5 py-2.5 text-sm"
            >
              清除
            </button>
          )}
        </form>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            {error}
          </div>
        )}

        <div className="text-sm text-[var(--text-muted)]">
          共 {decisions.length} 条决策记录
        </div>

        {decisions.length === 0 ? (
          <div className="rounded-2xl border border-[color:var(--border-subtle)] bg-[#f8f9fa] p-8 text-center">
            <div className="text-lg font-medium text-[var(--text-primary)]">暂无决策记录</div>
            <div className="mt-2 text-sm text-[var(--text-muted)]">
              使用决策查询功能后会自动记录
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {decisions.map((decision) => (
              <div
                key={decision.id}
                className="vw-card rounded-[24px] p-5 hover:border-[color:var(--accent-glow)]"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="vw-mono text-[11px] text-[var(--text-disabled)]">
                        {decision.id}
                      </span>
                      <span className="text-xs text-[var(--text-muted)]">
                        {new Date(decision.created_at).toLocaleString("zh-CN")}
                      </span>
                      {decision.evaluated_at && (
                        <span className="vw-badge vw-badge-success">已评估</span>
                      )}
                    </div>
                    
                    <div className="text-base font-medium text-[var(--text-primary)] mb-2">
                      {decision.query}
                    </div>
                    
                    {decision.recommended_cases.length > 0 && (
                      <div className="text-sm text-[var(--text-muted)] mb-2">
                        推荐案例: {decision.recommended_cases.join(", ")}
                      </div>
                    )}
                    
                    {decision.user_decision && (
                      <div className="text-sm text-[var(--text-secondary)] mb-1">
                        <span className="font-medium">用户决策:</span> {decision.user_decision}
                      </div>
                    )}
                    
                    {decision.actual_outcome && (
                      <div className="text-sm text-[var(--text-secondary)]">
                        <span className="font-medium">实际结果:</span> {decision.actual_outcome}
                      </div>
                    )}
                  </div>
                  
                  <div className="flex gap-2">
                    <Link
                      href={`/decisions/${decision.id}`}
                      className="vw-btn-secondary px-4 py-2 text-sm"
                    >
                      详情
                    </Link>
                    <button
                      onClick={() => handleDelete(decision.id)}
                      className="vw-btn-secondary px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                    >
                      删除
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
