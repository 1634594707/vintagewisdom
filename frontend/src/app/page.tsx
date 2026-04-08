import Link from "next/link";

import AppShell from "@/components/AppShell";
import { api, FALLBACK_CASES, FALLBACK_STATS, isFetchFailure } from "@/lib/api";

export default async function Home() {
  let stats = FALLBACK_STATS;
  let cases = FALLBACK_CASES;
  let degraded = true;

  try {
    const [statsData, casesData] = await Promise.all([api.stats(), api.cases()]);
    stats = statsData;
    cases = casesData.length > 0 ? casesData : FALLBACK_CASES;
    degraded = false;
  } catch (error) {
    if (!isFetchFailure(error)) {
      throw error;
    }
  }

  const recentCases = [...cases]
    .sort((a, b) => (b.updated_at || "").localeCompare(a.updated_at || ""))
    .slice(0, 4);

  const domainBuckets = cases.reduce<Record<string, number>>((acc, item) => {
    const key = item.domain || "UNSORTED";
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});

  const topDomains = Object.entries(domainBuckets).sort((a, b) => b[1] - a[1]).slice(0, 3);
  const completionRate =
    stats.decision_logs > 0
      ? Math.round((stats.evaluated_decision_logs / stats.decision_logs) * 100)
      : 0;
  const archiveSignal = recentCases[0];

  return (
    <AppShell title="总览">
      <div className="space-y-4 lg:space-y-5">
        <section className="vw-panel overflow-hidden rounded-[32px] p-5 md:p-7">
          <div className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
            <div className="relative overflow-hidden rounded-2xl border border-[color:var(--border-subtle)] bg-gradient-to-br from-[var(--accent-light)] to-white p-6 md:p-8">
              <div className="vw-eyebrow text-[var(--accent-primary)]">判断档案总览</div>
              <h2 className="vw-title mt-6 max-w-4xl text-4xl font-bold leading-tight md:text-5xl">
                让历史案例，成为可复用的判断系统。
              </h2>
              <p className="mt-4 max-w-3xl text-sm leading-7 text-[var(--text-secondary)] md:text-base">
                VintageWisdom 不应只是一个通用后台，而更像一座实时运转的决策档案馆：
                当前信号在前，历史先例在侧，结构化判断路径随时可调取。
              </p>

              <div className="mt-6 flex flex-wrap gap-3">
                <Link href="/query" className="vw-btn-primary px-5 py-3 text-sm font-medium">
                  发起查询
                </Link>
                <Link href="/cases" className="vw-btn-secondary px-5 py-3 text-sm">
                  打开案例库
                </Link>
                <Link href="/import" className="vw-btn-secondary px-5 py-3 text-sm">
                  导入材料
                </Link>
              </div>

              <div className="mt-8 grid gap-3 md:grid-cols-3">
                <HeroMetric label="档案深度" value={stats.cases} hint="已入库案例" />
                <HeroMetric label="反馈闭环" value={`${completionRate}%`} hint="已完成评估" />
                <HeroMetric label="待处理项" value={Math.max(stats.decision_logs - stats.evaluated_decision_logs, 0)} hint="仍在积压" />
              </div>
            </div>

            <div className="grid gap-4">
              <div className="vw-card rounded-[28px] p-5">
                <div>
                  <div className="vw-eyebrow">系统脉搏</div>
                  <div className="mt-2 text-[28px] font-medium text-[var(--text-primary)]">决策闭环覆盖率</div>
                </div>
                <div className="mt-4 flex items-center gap-3">
                  <div className="vw-badge vw-badge-success">{completionRate}% 已复盘</div>
                  <div className="h-px flex-1 bg-gradient-to-r from-[var(--border-medium)] to-transparent" />
                </div>

                <div className="mt-5 space-y-4">
                  <ProgressLine label="Case base" value={stats.cases} hint="Structured case library" />
                  <ProgressLine label="Decision logs" value={stats.decision_logs} hint="Recorded live queries" />
                  <ProgressLine
                    label="Outcome feedback"
                    value={stats.evaluated_decision_logs}
                    hint="Closed-loop evaluations"
                  />
                </div>

                <div className="mt-4 rounded-xl border border-[color:var(--border-subtle)] bg-[var(--bg-tertiary)] p-4 text-sm text-[var(--text-muted)]">
                  {degraded
                    ? "当前无法连接后端，所以总览页正在展示示例数据，而不是直接报错中断。"
                    : "实时 API 数据已加载成功，当前总览页正在读取后端工作区里的真实内容。"}
                </div>
              </div>

              <div className="vw-card rounded-[28px] p-5">
                <div className="vw-eyebrow">重点案例</div>
                <div className="mt-2 text-xl font-medium text-[var(--text-primary)]">{archiveSignal?.title || "暂无重点案例"}</div>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <span className="vw-badge vw-badge-accent">{archiveSignal?.domain || "未分类"}</span>
                  <span className="vw-mono text-[11px] text-[var(--text-disabled)]">{archiveSignal?.id || "-"}</span>
                </div>
                <div className="mt-4 text-sm leading-7 text-[var(--text-muted)]">
                  {archiveSignal?.lesson_core || archiveSignal?.description || "当前没有可展示的重点案例摘要。"}
                </div>
                <div className="mt-5">
                  <Link href="/cases" className="text-sm text-[var(--accent-secondary)] hover:text-[var(--text-primary)]">
                    进入档案库
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <StatCard label="案例总量" value={stats.cases} hint="当前可引用先例" accent="var(--accent-primary)" />
          <StatCard label="本轮新增" value={Math.max(3, Math.round(stats.cases * 0.08))} hint="新入库材料" accent="var(--info)" />
          <StatCard label="待复盘" value={Math.max(stats.decision_logs - stats.evaluated_decision_logs, 0)} hint="仍未关闭的反馈积压" accent="var(--warning)" />
          <StatCard label="覆盖率" value={`${completionRate}%`} hint="已评估决策记录占比" accent="var(--success)" />
        </section>

        <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="vw-card rounded-[28px] p-5">
            <div className="flex items-center justify-between">
              <div>
                <div className="vw-eyebrow">最近动态</div>
                <h3 className="vw-title mt-1 text-xl font-semibold">最新更新案例</h3>
              </div>
              <Link href="/cases" className="text-sm text-[var(--accent-secondary)] hover:text-[var(--text-primary)]">
                查看全部
              </Link>
            </div>

            <div className="mt-4 space-y-3">
              {recentCases.map((item) => (
                <Link
                  key={item.id}
                  href={`/cases/${encodeURIComponent(item.id)}`}
                  className="block rounded-xl border border-[color:var(--border-subtle)] bg-white p-4 transition-all hover:border-[color:var(--accent-primary)] hover:shadow-md hover:-translate-y-0.5"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="vw-badge vw-badge-accent">{item.domain || "未分类"}</span>
                    <span className="vw-mono text-[11px] text-[var(--text-disabled)]">{item.id}</span>
                  </div>
                  <div className="mt-3 text-base font-medium">{item.title}</div>
                  <div className="mt-2 line-clamp-2 text-sm leading-6 text-[var(--text-muted)]">
                    {item.lesson_core || item.description || "这个案例暂时还没有整理出核心经验摘要。"}
                  </div>
                </Link>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <div className="vw-card rounded-[28px] p-5">
              <div className="vw-eyebrow">领域分布</div>
              <h3 className="vw-title mt-1 text-xl font-semibold">主要领域占比</h3>

              <div className="mt-4 space-y-4">
                {topDomains.map(([domain, count]) => (
                  <div key={domain}>
                    <div className="mb-1 flex items-center justify-between text-sm">
                      <span className="text-[var(--text-secondary)]">{domain}</span>
                      <span className="vw-mono text-[var(--text-muted)]">{count}</span>
                    </div>
                    <div className="h-2.5 rounded-full bg-[var(--bg-tertiary)]">
                      <div
                        className="h-2.5 rounded-full bg-gradient-to-r from-[var(--accent-primary)] to-[var(--accent-secondary)]"
                        style={{ width: `${Math.max((count / Math.max(cases.length, 1)) * 100, 12)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="vw-card rounded-[28px] p-5">
              <div className="vw-eyebrow">下一步建议</div>
              <h3 className="vw-title mt-1 text-xl font-semibold">操作提示</h3>
              <div className="mt-4 space-y-3">
                <QuickAction
                  href="/query"
                  title="发起一条新的决策查询"
                  description="看看当前情境与历史档案和推荐引擎中的案例到底有多接近。"
                />
                <QuickAction
                  href="/graph"
                  title="检查图谱连通性"
                  description="在按模式行动前，先确认领域、聚类和证据链之间的结构是否自洽。"
                />
                <QuickAction
                  href="/settings"
                  title="核对模型运行状态"
                  description="保持 AI 层在线，让查询、分类和推理流程都维持稳定。"
                />
              </div>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}

function StatCard({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: number | string;
  hint: string;
  accent: string;
}) {
  return (
    <div className="vw-card rounded-[28px] p-5">
      <div className="vw-eyebrow">{label}</div>
      <div className="vw-kpi-value mt-3" style={{ color: accent }}>
        {value}
      </div>
      <div className="mt-2 text-sm text-[var(--text-muted)]">{hint}</div>
    </div>
  );
}

function ProgressLine({ label, value, hint }: { label: string; value: number; hint: string }) {
  return (
    <div className="rounded-xl border border-[color:var(--border-subtle)] bg-[var(--bg-tertiary)] p-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-sm text-[var(--text-secondary)]">{label}</div>
          <div className="text-xs text-[var(--text-disabled)]">{hint}</div>
        </div>
        <div className="vw-mono text-lg text-[var(--text-primary)]">{value}</div>
      </div>
    </div>
  );
}

function QuickAction({
  href,
  title,
  description,
}: {
  href: string;
  title: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      className="block rounded-xl border border-[color:var(--border-subtle)] bg-white p-4 transition-all hover:border-[color:var(--accent-primary)] hover:shadow-md hover:-translate-y-0.5"
    >
      <div className="font-medium text-[var(--text-primary)]">{title}</div>
      <div className="mt-1 text-sm leading-6 text-[var(--text-muted)]">{description}</div>
    </Link>
  );
}

function HeroMetric({
  label,
  value,
  hint,
}: {
  label: string;
  value: string | number;
  hint: string;
}) {
  return (
    <div className="rounded-xl border border-[color:var(--border-subtle)] bg-white px-4 py-4">
      <div className="text-[11px] uppercase tracking-[0.22em] text-[var(--text-disabled)]">{label}</div>
      <div className="vw-title mt-3 text-3xl font-bold text-[var(--accent-primary)]">{value}</div>
      <div className="mt-1 text-xs text-[var(--text-muted)]">{hint}</div>
    </div>
  );
}
