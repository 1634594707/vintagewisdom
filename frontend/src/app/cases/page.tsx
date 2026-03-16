import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";

export default async function CasesPage({
  searchParams,
}: {
  searchParams?: Promise<{ q?: string }>;
}) {
  const cases = await api.cases();
  const sp = (await searchParams) || {};
  const q = (sp?.q || "").trim().toLowerCase();
  const filtered = q
    ? cases.filter((c) =>
        c.id.toLowerCase().includes(q) || c.title.toLowerCase().includes(q) || (c.domain || "").toLowerCase().includes(q)
      )
    : cases;

  return (
    <AppShell title="案例库">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-[var(--text-secondary)]">总数</div>
            <div className="text-2xl font-semibold">{filtered.length}</div>
          </div>
          <form className="flex items-center gap-2" action="/cases">
            <input
              name="q"
              defaultValue={sp?.q || ""}
              placeholder="搜索 ID / 标题 / 领域"
              className="h-9 w-72 rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] px-3 text-sm text-[var(--text-primary)] outline-none focus:border-[color:var(--accent-primary)]"
            />
            <button
              type="submit"
              className="rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] px-3 py-2 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            >
              搜索
            </button>
          </form>
        </div>

        <div className="rounded-lg border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)]">
          <div className="grid grid-cols-[180px_140px_1fr] gap-3 border-b border-[color:var(--bg-tertiary)] px-4 py-3 text-xs text-[var(--text-muted)]">
            <div>ID</div>
            <div>领域</div>
            <div>标题</div>
          </div>
          <div className="divide-y divide-[color:var(--bg-tertiary)]">
            {filtered.map((c) => (
              <div key={c.id} className="grid grid-cols-[180px_140px_1fr] gap-3 px-4 py-3 text-sm">
                <div className="font-mono text-[13px] text-[var(--text-secondary)]">{c.id}</div>
                <div className="text-[var(--text-secondary)]">{c.domain}</div>
                <div className="truncate">{c.title}</div>
              </div>
            ))}
            {filtered.length === 0 ? (
              <div className="px-4 py-10 text-sm text-[var(--text-secondary)]">
                暂无案例。你可以先导入 CSV 作为知识库。
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
