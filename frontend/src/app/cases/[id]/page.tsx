import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";

export default async function CaseDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const c = await api.case(id);

  return (
    <AppShell title="案例详情">
      <div className="space-y-4">
        <div className="rounded-lg border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-4">
          <div className="text-xs text-[var(--text-muted)]">ID</div>
          <div className="mt-1 font-mono text-sm text-[var(--text-primary)] break-all">{c.id}</div>

          <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
            <div>
              <div className="text-xs text-[var(--text-muted)]">领域</div>
              <div className="mt-1 text-sm text-[var(--text-primary)]">{c.domain}</div>
            </div>
            <div>
              <div className="text-xs text-[var(--text-muted)]">更新时间</div>
              <div className="mt-1 text-sm text-[var(--text-primary)]">{c.updated_at || "-"}</div>
            </div>
          </div>

          <div className="mt-4">
            <div className="text-xs text-[var(--text-muted)]">标题</div>
            <div className="mt-1 text-base font-medium text-[var(--text-primary)]">{c.title}</div>
          </div>
        </div>

        <Section title="描述" value={c.description} />
        <Section title="决策节点" value={c.decision_node} />
        <Section title="采取行动" value={c.action_taken} />
        <Section title="结果" value={c.outcome_result} />
        <Section title="时间线" value={c.outcome_timeline} />
        <Section title="核心教训" value={c.lesson_core} />
      </div>
    </AppShell>
  );
}

function Section({ title, value }: { title: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="rounded-lg border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-4">
      <div className="text-sm font-medium text-[var(--text-primary)]">{title}</div>
      <div className="mt-2 whitespace-pre-wrap text-sm text-[var(--text-secondary)]">{value}</div>
    </div>
  );
}
