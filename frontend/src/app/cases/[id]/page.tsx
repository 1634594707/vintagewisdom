import Link from "next/link";

import AppShell from "@/components/AppShell";
import { api, FALLBACK_CASES, isFetchFailure } from "@/lib/api";

export default async function CaseDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let degraded = false;
  let c = FALLBACK_CASES.find((item) => item.id === id) || FALLBACK_CASES[0];

  try {
    c = await api.case(id);
  } catch (error) {
    if (!isFetchFailure(error)) {
      throw error;
    }
    degraded = true;
  }

  return (
    <AppShell title="案例细读">
      <div className="space-y-4">
        <section className="vw-panel rounded-[28px] p-5 md:p-6">
          <Link href="/cases" className="text-sm text-[var(--accent-secondary)] hover:text-[var(--text-primary)]">
            返回案例库
          </Link>

          <div className="mt-4 flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="vw-badge vw-badge-accent">{c.domain || "未分类"}</span>
                <span className="vw-mono text-[11px] text-[var(--text-disabled)]">{c.id}</span>
                {degraded ? <span className="vw-badge vw-badge-warning">示例回退</span> : null}
              </div>
              <h2 className="vw-title mt-3 text-3xl font-semibold">{c.title}</h2>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-[var(--text-muted)]">
                {c.description || "这个案例暂时还没有更完整的背景叙述。"}
              </p>
              
              <div className="mt-4 flex flex-wrap gap-2">
                <Link 
                  href={`/cases/${id}/edit`}
                  className="vw-btn-primary px-4 py-2 text-sm font-medium"
                >
                  编辑案例
                </Link>
                <Link 
                  href={`/cases/${id}/versions`}
                  className="vw-btn-secondary px-4 py-2 text-sm"
                >
                  版本历史
                </Link>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <MetaCard label="最近更新" value={c.updated_at || "-"} />
              <MetaCard label="创建时间" value={c.created_at || "-"} />
              <MetaCard label="置信度" value={c.confidence || "-"} />
            </div>
          </div>
        </section>

        <section className="grid gap-4 xl:grid-cols-[1.08fr_0.92fr]">
          <div className="space-y-4">
            <Section title="决策节点" value={c.decision_node} />
            <Section title="采取动作" value={c.action_taken} />
            <Section title="结果表现" value={c.outcome_result} />
            <Section title="结果时间线" value={c.outcome_timeline} />
          </div>

          <div className="space-y-4">
            <Section title="核心经验" value={c.lesson_core} highlight />
            <div className="vw-card rounded-[24px] p-5">
              <div className="vw-eyebrow">复盘提示</div>
              <div className="mt-3 space-y-3 text-sm leading-6 text-[var(--text-secondary)]">
                <PromptItem text="这个案例里，哪些约束是真结构性问题，哪些只是当时看起来像结构性问题？" />
                <PromptItem text="如果提前一个决策节点介入，最可能改变走向的变量是什么？" />
                <PromptItem text="哪些经验可以迁移到别的领域，哪些不该直接照搬？" />
              </div>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}

function MetaCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[color:var(--border-subtle)] bg-[#f8f9fa] p-3">
      <div className="text-[11px] uppercase tracking-[0.18em] text-[var(--text-disabled)]">{label}</div>
      <div className="mt-2 text-sm text-[var(--text-secondary)]">{value}</div>
    </div>
  );
}

function Section({
  title,
  value,
  highlight = false,
}: {
  title: string;
  value?: string | null;
  highlight?: boolean;
}) {
  if (!value) return null;

  return (
    <div
      className={
        highlight
          ? "vw-card rounded-[24px] border-[color:var(--accent-glow)] p-5"
          : "vw-card rounded-[24px] p-5"
      }
    >
      <div className="vw-eyebrow">{title}</div>
      <div className="mt-3 whitespace-pre-wrap text-sm leading-7 text-[var(--text-secondary)]">{value}</div>
    </div>
  );
}

function PromptItem({ text }: { text: string }) {
  return (
    <div className="rounded-2xl border border-[color:var(--border-subtle)] bg-[#f8f9fa] p-3">
      {text}
    </div>
  );
}
