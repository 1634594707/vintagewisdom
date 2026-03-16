"use client";

import { useEffect, useState } from "react";

import AppShell from "@/components/AppShell";
import { api, QueryResponse } from "@/lib/api";

const STORAGE_KEY = "vintagewisdom_query_result";
const STORAGE_TEXT = "vintagewisdom_query_text";
const STORAGE_SHOW_RESULT = "vintagewisdom_query_show_result";

export default function QueryPage() {
  // 初始状态（用于 SSR）
  const [text, setText] = useState<string>("");
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [showResult, setShowResult] = useState<boolean>(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [saving, setSaving] = useState(false);
  const [savedId, setSavedId] = useState<string>("");
  const [analyzing, setAnalyzing] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);

  // 客户端 hydration 完成后恢复状态
  useEffect(() => {
    try {
      const savedText = localStorage.getItem(STORAGE_TEXT);
      const savedResult = localStorage.getItem(STORAGE_KEY);
      const savedShowResult = localStorage.getItem(STORAGE_SHOW_RESULT);

      if (savedText) setText(savedText);
      if (savedResult) {
        try {
          const parsed = JSON.parse(savedResult);
          setResult(parsed);
        } catch {}
      }
      if (savedShowResult === "true") {
        setShowResult(true);
      }
    } catch (e) {
      console.error("Failed to restore state:", e);
    }
    setIsHydrated(true);
  }, []);

  // 同步状态到 localStorage
  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(STORAGE_TEXT, text);
  }, [text, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    if (result) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(result));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [result, isHydrated]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(STORAGE_SHOW_RESULT, showResult.toString());
  }, [showResult, isHydrated]);

  async function onSubmit() {
    const q = text.trim();
    if (!q) return;

    setAnalyzing(true);
    setLoading(true);
    setError("");
    setSavedId("");
    setShowResult(false);

    try {
      const r = await api.query(q);
      setResult(r);
      setShowResult(true);
    } catch (e) {
      setResult(null);
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
      setTimeout(() => setAnalyzing(false), 500);
    }
  }

  async function onSaveDecision() {
    if (!result) return;
    const q = text.trim();
    if (!q) return;

    setSaving(true);
    setError("");
    setSavedId("");
    try {
      const resp = await api.createDecision({
        query: q,
        recommended_cases: result.cases.map((c) => c.id),
        context: {
          source: "web.query",
          reasoning: result.reasoning,
          recommendations: result.recommendations,
        },
      });
      setSavedId(resp.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  function onClear() {
    setResult(null);
    setText("");
    setShowResult(false);
    setError("");
    setSavedId("");
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(STORAGE_TEXT);
    localStorage.removeItem(STORAGE_SHOW_RESULT);
  }

  function onNewQuery() {
    setShowResult(false);
    setError("");
    setSavedId("");
  }

  // 分析中界面
  if (analyzing) {
    return (
      <AppShell title="决策查询">
        <div className="flex h-[calc(100vh-120px)] flex-col items-center justify-center">
          <div className="relative">
            <div className="h-24 w-24 animate-spin rounded-full border-4 border-[var(--bg-tertiary)] border-t-[var(--accent-primary)]" />
            <div
              className="absolute inset-0 m-4 animate-spin rounded-full border-4 border-[var(--bg-tertiary)] border-b-[var(--accent-primary)]"
              style={{ animationDirection: "reverse", animationDuration: "1.5s" }}
            />
          </div>
          <div className="mt-8 text-center">
            <div className="text-lg font-medium text-[var(--text-primary)]">AI 正在分析...</div>
            <div className="mt-2 text-sm text-[var(--text-muted)]">正在检索相关案例并生成建议</div>
          </div>
          <div className="mt-8 max-w-md rounded-lg border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-4">
            <div className="text-xs text-[var(--text-muted)]">当前查询：</div>
            <div className="mt-1 text-sm text-[var(--text-primary)] line-clamp-2">{text}</div>
          </div>
        </div>
      </AppShell>
    );
  }

  // 显示结果界面
  if (showResult && result) {
    return (
      <AppShell title="决策查询">
        <div className="space-y-6">
          <div className="flex items-center justify-between rounded-lg border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] px-4 py-3">
            <div className="flex items-center gap-3">
              <span className="text-sm text-[var(--text-muted)]">查询：</span>
              <span className="text-sm text-[var(--text-primary)] line-clamp-1 max-w-md">{text}</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onNewQuery}
                className="rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] px-3 py-1.5 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              >
                新查询
              </button>
              <button
                type="button"
                onClick={onClear}
                className="rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] px-3 py-1.5 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              >
                清除
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="lg:col-span-1">
              <div className="rounded-lg border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium">匹配案例</div>
                  <span className="rounded-full bg-[var(--accent-primary)] px-2 py-0.5 text-xs text-white">
                    {result.matches}
                  </span>
                </div>
                <div className="mt-4 space-y-3 max-h-[400px] overflow-y-auto">
                  {result.cases.map((c) => (
                    <div
                      key={c.id}
                      className="rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] p-3 hover:border-[color:var(--accent-primary)] transition-colors"
                    >
                      <div className="flex items-center gap-2 text-xs text-[var(--text-muted)]">
                        <span className="font-mono">{c.id}</span>
                        <span>·</span>
                        <span className="text-[var(--accent-primary)]">{c.domain}</span>
                      </div>
                      <div className="mt-1 text-sm text-[var(--text-primary)]">{c.title}</div>
                    </div>
                  ))}
                  {result.cases.length === 0 && (
                    <div className="text-center py-8 text-sm text-[var(--text-muted)]">暂无匹配案例</div>
                  )}
                </div>
                {result.cases.length > 0 && (
                  <button
                    type="button"
                    onClick={onSaveDecision}
                    disabled={saving}
                    className="mt-4 w-full rounded-md bg-[var(--accent-primary)] px-3 py-2 text-sm text-white hover:bg-[var(--accent-hover)] disabled:opacity-50"
                  >
                    {saving ? "保存中..." : "保存为决策记录"}
                  </button>
                )}
                {savedId && (
                  <div className="mt-2 text-center text-xs text-green-400">已保存，ID: {savedId}</div>
                )}
              </div>
            </div>

            <div className="lg:col-span-2 space-y-6">
              <div className="rounded-lg border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-4">
                <div className="text-sm font-medium">AI 推理分析</div>
                <div className="mt-4 rounded-md bg-[var(--bg-primary)] p-4">
                  <pre className="whitespace-pre-wrap break-words text-sm text-[var(--text-secondary)] leading-relaxed">
                    {result.reasoning}
                  </pre>
                </div>
              </div>

              <div className="rounded-lg border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-4">
                <div className="text-sm font-medium">行动建议</div>
                <div className="mt-4 space-y-3">
                  {result.recommendations.map((r, idx) => (
                    <div key={idx} className="flex gap-3 rounded-md bg-[var(--bg-primary)] p-4">
                      <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[var(--accent-primary)] text-xs text-white">
                        {idx + 1}
                      </div>
                      <div className="text-sm text-[var(--text-secondary)] leading-relaxed">{r}</div>
                    </div>
                  ))}
                  {result.recommendations.length === 0 && (
                    <div className="text-center py-8 text-sm text-[var(--text-muted)]">暂无建议</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </AppShell>
    );
  }

  // 初始输入界面
  return (
    <AppShell title="决策查询">
      <div className="flex h-[calc(100vh-120px)] flex-col items-center justify-center px-4">
        <div className="w-full max-w-2xl">
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-medium text-[var(--text-primary)]">决策助手</h1>
            <p className="mt-2 text-sm text-[var(--text-muted)]">
              描述你的决策情境，AI 将基于历史案例为你提供分析和建议
            </p>
          </div>

          <div className="rounded-xl border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-6 shadow-lg">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={5}
              className="w-full resize-none rounded-lg border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] px-4 py-3 text-base text-[var(--text-primary)] outline-none transition-colors focus:border-[color:var(--accent-primary)]"
              placeholder="例如：我是一个A轮公司CTO，技术债很重，想重构但业务压力大，该如何决策？"
              onKeyDown={(e) => {
                if (e.key === "Enter" && e.metaKey) {
                  onSubmit();
                }
              }}
            />

            <div className="mt-4 flex items-center justify-between">
              <div className="text-xs text-[var(--text-muted)]">按 Cmd + Enter 快速提交</div>
              <button
                type="button"
                onClick={onSubmit}
                disabled={loading || !text.trim()}
                className="rounded-lg bg-[var(--accent-primary)] px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-[var(--accent-hover)] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? "分析中..." : "开始分析"}
              </button>
            </div>

            {error && (
              <div className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
                {error}
              </div>
            )}
          </div>

          <div className="mt-8">
            <div className="text-xs text-[var(--text-muted)] mb-3">示例查询：</div>
            <div className="flex flex-wrap gap-2">
              {["是否接受 offer / 跳槽", "是否重构核心模块", "是否投资某个项目", "是否买房"].map(
                (example) => (
                  <button
                    key={example}
                    type="button"
                    onClick={() => setText(example)}
                    className="rounded-full border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] px-3 py-1.5 text-xs text-[var(--text-secondary)] transition-colors hover:border-[color:var(--accent-primary)] hover:text-[var(--text-primary)]"
                  >
                    {example}
                  </button>
                )
              )}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
