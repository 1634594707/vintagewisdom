"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import AppShell from "@/components/AppShell";
import { api, type QueryResponse } from "@/lib/api";

const STORAGE_KEY = "vintagewisdom_query_result";
const STORAGE_TEXT = "vintagewisdom_query_text";
const STORAGE_SHOW_RESULT = "vintagewisdom_query_show_result";

const EXAMPLES = [
  "平台团队技术债不断上升，但交付压力依旧很高，现在应该整体重构还是分阶段迁移？",
  "我手上有一个高现金的新 offer，应该怎样和当前岗位的长期成长空间一起比较？",
  "有哪些历史案例和“改革被既有利益集团阻断”这类局面最接近？",
  "当收入压力和组织债务同时上升时，管理团队应该如何安排变革顺序？",
];

export default function QueryPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [savedId, setSavedId] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    try {
      const savedText = localStorage.getItem(STORAGE_TEXT);
      const savedResult = localStorage.getItem(STORAGE_KEY);
      const savedShowResult = localStorage.getItem(STORAGE_SHOW_RESULT);

      if (savedText) setText(savedText);
      if (savedResult) {
        try {
          setResult(JSON.parse(savedResult));
        } catch {}
      }
      if (savedShowResult === "true") setShowResult(true);
    } catch (e) {
      console.error("Failed to restore query state:", e);
    }
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(STORAGE_TEXT, text);
  }, [isHydrated, text]);

  useEffect(() => {
    if (!isHydrated) return;
    if (result) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(result));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [isHydrated, result]);

  useEffect(() => {
    if (!isHydrated) return;
    localStorage.setItem(STORAGE_SHOW_RESULT, String(showResult));
  }, [isHydrated, showResult]);

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
      setTimeout(() => setAnalyzing(false), 450);
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

  const reasoningSections = useMemo(() => splitReasoning(result?.reasoning ?? ""), [result?.reasoning]);

  if (analyzing) {
    return (
      <AppShell title="决策查询">
        <div className="flex min-h-[70dvh] items-center justify-center">
          <div className="vw-panel max-w-xl rounded-[28px] px-8 py-10 text-center">
            <div className="mx-auto h-20 w-20 animate-spin rounded-full border-4 border-[rgba(196,167,130,0.16)] border-t-[var(--accent-primary)]" />
            <h2 className="vw-title mt-6 text-[40px] font-semibold">正在整理判断线索</h2>
            <p className="mt-3 text-sm leading-6 text-[var(--text-muted)]">
              系统正在召回相似案例，整理风险提醒，并把它们收敛成更容易执行的建议。
            </p>
            <div className="mt-6 rounded-xl border border-[color:var(--border-subtle)] bg-[var(--bg-tertiary)] p-4 text-left">
              <div className="vw-eyebrow">当前问题</div>
              <div className="mt-2 text-sm leading-6 text-[var(--text-secondary)]">{text}</div>
            </div>
          </div>
        </div>
      </AppShell>
    );
  }

  if (showResult && result) {
    return (
      <AppShell title="决策查询">
        <div className="space-y-4">
          <section className="vw-panel rounded-[28px] p-5 md:p-6">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div className="max-w-4xl">
                <div className="vw-eyebrow">问题快照</div>
                <h2 className="vw-title mt-2 text-[40px] font-semibold">当前判断问题</h2>
                <p className="mt-3 text-sm leading-7 text-[var(--text-secondary)]">{text}</p>
              </div>

              <div className="flex flex-wrap gap-2">
                <button type="button" onClick={onNewQuery} className="vw-btn-secondary px-4 py-2 text-sm">
                  重新提问
                </button>
                <button type="button" onClick={onClear} className="vw-btn-secondary px-4 py-2 text-sm">
                  清空
                </button>
                <button
                  type="button"
                  onClick={onSaveDecision}
                  disabled={saving}
                  className="vw-btn-primary px-4 py-2 text-sm font-medium disabled:opacity-60"
                >
                  {saving ? "正在保存..." : "保存决策记录"}
                </button>
              </div>
            </div>

            {savedId ? (
              <div className="mt-4 rounded-xl border border-[color:var(--success)] bg-[var(--success-light)] px-4 py-3 text-sm text-[var(--success)]">
                已保存决策记录，编号为 <span className="vw-mono">{savedId}</span>
              </div>
            ) : null}

            {error ? (
              <div className="mt-4 rounded-xl border border-[color:var(--error)] bg-[var(--error-light)] px-4 py-3 text-sm text-[var(--error)]">
                {error}
              </div>
            ) : null}
          </section>

          <section className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <div className="space-y-4">
              <div className="vw-card rounded-[24px] p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="vw-eyebrow">案例召回</div>
                    <h3 className="vw-title mt-1 text-[34px] font-semibold">相关案例</h3>
                  </div>
                  <div className="vw-badge vw-badge-accent">{result.matches} 条命中</div>
                </div>

                <div className="vw-scrollbar mt-4 max-h-[620px] space-y-3 overflow-y-auto pr-1">
                  {result.cases.length > 0 ? (
                    result.cases.map((c) => (
                      <Link
                        key={c.id}
                        href={`/cases/${encodeURIComponent(c.id)}`}
                        className="block rounded-xl border border-[color:var(--border-subtle)] bg-white p-4 transition-all hover:border-[color:var(--accent-primary)] hover:shadow-md hover:-translate-y-0.5"
                      >
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="vw-badge vw-badge-accent">{c.domain || "未分类"}</span>
                          <span className="vw-mono text-[11px] text-[var(--text-disabled)]">{c.id}</span>
                          {c.confidence ? <span className="vw-badge">{renderConfidence(c.confidence)}</span> : null}
                        </div>
                        <div className="mt-2 text-sm font-medium text-[var(--text-primary)]">{c.title}</div>
                        <div className="mt-2 line-clamp-2 text-sm leading-6 text-[var(--text-muted)]">
                          {c.lesson_core || c.description || "暂时还没有可展示的摘要。"}
                        </div>
                        <div className="mt-3 grid gap-2 sm:grid-cols-2">
                          <MiniInfo label="结果" value={c.outcome_result || "待补充"} />
                          <MiniInfo label="时间窗" value={c.outcome_timeline || "待补充"} />
                        </div>
                      </Link>
                    ))
                  ) : (
                    <EmptyState label="没有找到足够接近的案例" hint="可以补充角色、约束、时间窗口和希望达成的结果。" />
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="vw-card rounded-[24px] p-5">
                <div className="vw-eyebrow">判断摘要</div>
                <h3 className="vw-title mt-1 text-[34px] font-semibold">AI 分析</h3>
                <div className="mt-4 space-y-3">
                  <ResultPanel
                    title="核心判断"
                    content={reasoningSections.summary}
                    empty="系统还没有生成明确结论，可以尝试补充更多上下文。"
                  />
                  <ResultPanel
                    title="风险提醒"
                    content={reasoningSections.risks}
                    empty="当前没有额外的风险提醒。"
                  />
                </div>
              </div>

              <div className="vw-card rounded-[24px] p-5">
                <div className="vw-eyebrow">行动建议</div>
                <h3 className="vw-title mt-1 text-[34px] font-semibold">建议路径</h3>
                <div className="mt-4 space-y-3">
                  {result.recommendations.length > 0 ? (
                    result.recommendations.map((recommendation, idx) => (
                      <div
                        key={`${recommendation}-${idx}`}
                        className="flex gap-4 rounded-xl border border-[color:var(--border-subtle)] bg-white p-4"
                      >
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] text-sm font-semibold text-white">
                          {idx + 1}
                        </div>
                        <div className="text-sm leading-7 text-[var(--text-secondary)]">{recommendation}</div>
                      </div>
                    ))
                  ) : (
                    <EmptyState label="当前没有返回建议" hint="可以检查 AI 状态，或缩小问题范围后重新查询。" />
                  )}
                </div>
              </div>
            </div>
          </section>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell title="决策查询">
      <div className="grid gap-4 xl:grid-cols-[1.12fr_0.88fr]">
        <section className="vw-panel rounded-[28px] p-5 md:p-6">
          <div className="vw-eyebrow">决策助手</div>
          <h2 className="vw-title mt-2 text-[44px] font-semibold md:text-[54px]">先把问题说清楚，再让系统回看历史。</h2>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--text-muted)]">
            尽量写清角色、限制、时间窗口和你正在权衡的选择。系统会将你的问题与历史案例进行比对，并返回判断摘要与行动建议。
          </p>

          <div className="mt-6 rounded-xl border border-[color:var(--border-subtle)] bg-white p-4">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={8}
              className="vw-textarea min-h-[220px] resize-none rounded-xl px-4 py-4 text-base leading-7"
              placeholder="例如：我负责一个平台团队，技术债和线上事故都在升高，但业务交付压力依然很大。现在应该一次性重构底层，还是在两个季度内分阶段迁移？"
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) onSubmit();
              }}
            />

            <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="text-xs text-[var(--text-muted)]">支持 Ctrl/Cmd + Enter 快速提交。</div>
              <button
                type="button"
                onClick={onSubmit}
                disabled={loading || !text.trim()}
                className="vw-btn-primary px-5 py-2.5 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? "分析中..." : "开始分析"}
              </button>
            </div>

            {error ? (
              <div className="mt-4 rounded-xl border border-[color:var(--error)] bg-[var(--error-light)] px-4 py-3 text-sm text-[var(--error)]">
                {error}
              </div>
            ) : null}
          </div>
        </section>

        <section className="space-y-4">
          <div className="vw-card rounded-[24px] p-5">
            <div className="vw-eyebrow">示例提问</div>
            <h3 className="vw-title mt-1 text-[34px] font-semibold">起始问题</h3>
            <div className="mt-4 flex flex-wrap gap-2">
              {EXAMPLES.map((example) => (
                <button
                  key={example}
                  type="button"
                  onClick={() => setText(example)}
                  className="rounded-full border border-[color:var(--border-subtle)] bg-white px-3 py-2 text-sm text-[var(--text-secondary)] transition-all hover:border-[color:var(--accent-primary)] hover:text-[var(--accent-primary)]"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>

          <div className="vw-card rounded-[24px] p-5">
            <div className="vw-eyebrow">输出结构</div>
            <h3 className="vw-title mt-1 text-[34px] font-semibold">你会得到什么</h3>
            <div className="mt-4 space-y-3">
              <InfoRow title="相关案例" description="系统会优先找出与你当前处境最接近的历史案例，作为判断参照。" />
              <InfoRow title="核心判断" description="系统会先给出结论摘要，再补充关键风险，而不是丢给你一整块原始文本。" />
              <InfoRow title="行动建议" description="建议会尽量组织成可以直接执行的下一步，而不是停留在泛泛而谈。" />
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}

function InfoRow({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-xl border border-[color:var(--border-subtle)] bg-white p-4">
      <div className="font-medium text-[var(--text-primary)]">{title}</div>
      <div className="mt-1 text-sm leading-6 text-[var(--text-muted)]">{description}</div>
    </div>
  );
}

function EmptyState({ label, hint }: { label: string; hint: string }) {
  return (
    <div className="rounded-xl border border-dashed border-[color:var(--border-strong)] bg-[var(--bg-tertiary)] p-5 text-center">
      <div className="text-sm font-medium text-[var(--text-primary)]">{label}</div>
      <div className="mt-2 text-sm text-[var(--text-muted)]">{hint}</div>
    </div>
  );
}

function ResultPanel({
  title,
  content,
  empty,
}: {
  title: string;
  content: string[];
  empty: string;
}) {
  return (
    <div className="rounded-xl border border-[color:var(--border-subtle)] bg-[var(--bg-tertiary)] p-4">
      <div className="text-sm font-medium text-[var(--text-primary)]">{title}</div>
      <div className="mt-3 space-y-2">
        {content.length > 0 ? (
          content.map((item, index) => (
            <div key={`${title}-${index}`} className="text-sm leading-7 text-[var(--text-secondary)]">
              {item}
            </div>
          ))
        ) : (
          <div className="text-sm leading-7 text-[var(--text-muted)]">{empty}</div>
        )}
      </div>
    </div>
  );
}

function MiniInfo({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[color:var(--border-subtle)] bg-[var(--bg-tertiary)] px-3 py-2">
      <div className="text-[11px] uppercase tracking-[0.16em] text-[var(--text-disabled)]">{label}</div>
      <div className="mt-1 text-xs leading-5 text-[var(--text-secondary)]">{value}</div>
    </div>
  );
}

function renderConfidence(value: string) {
  const normalized = value.toLowerCase();
  if (normalized === "high") return "高置信度";
  if (normalized === "medium") return "中置信度";
  if (normalized === "low") return "低置信度";
  return value;
}

function splitReasoning(reasoning: string) {
  const cleaned = reasoning
    .replace(/\[RedTeam(?:-LLM)?\]/gi, "风险提醒：")
    .replace(/\r/g, "")
    .trim();

  if (!cleaned) {
    return { summary: [], risks: [] };
  }

  const blocks = cleaned
    .split(/\n{2,}/)
    .map((item) => item.trim())
    .filter(Boolean);

  const summary: string[] = [];
  const risks: string[] = [];

  for (const block of blocks) {
    if (/风险提醒|Facts:|Logic:|Assumptions:|WorstCase:|Mitigation:|OpportunityCost:|Reversibility:/i.test(block)) {
      risks.push(toChineseRiskBlock(block));
    } else {
      summary.push(block);
    }
  }

  return { summary, risks };
}

function toChineseRiskBlock(input: string) {
  return input
    .replace(/Facts:/gi, "事实校验：")
    .replace(/Logic:/gi, "逻辑挑战：")
    .replace(/Assumptions:/gi, "隐含假设：")
    .replace(/WorstCase:/gi, "最坏情况：")
    .replace(/Mitigation:/gi, "缓解动作：")
    .replace(/OpportunityCost:/gi, "机会成本：")
    .replace(/Reversibility:/gi, "可逆性：")
    .replace(/\(evidence:[^)]+\)/gi, "")
    .replace(/\s+/g, " ")
    .trim();
}
