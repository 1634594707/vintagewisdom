import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";

export default async function Home() {
  const stats = await api.stats();
  return (
    <AppShell title="仪表盘">
      <div className="grid grid-cols-3 gap-4">
        <StatCard label="案例数" value={stats.cases} />
        <StatCard label="决策记录" value={stats.decision_logs} />
        <StatCard label="已评估" value={stats.evaluated_decision_logs} />
      </div>
    </AppShell>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-5">
      <div className="text-xs text-[var(--text-muted)]">{label}</div>
      <div className="mt-2 text-3xl font-semibold text-[var(--accent-primary)]">{value}</div>
    </div>
  );
}
