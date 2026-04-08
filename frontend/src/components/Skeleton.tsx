export function CaseCardSkeleton() {
  return (
    <div className="vw-card animate-pulse rounded-xl p-5">
      <div className="flex items-center gap-2">
        <div className="h-6 w-20 rounded-full bg-[var(--bg-tertiary)]" />
        <div className="h-4 w-32 rounded bg-[var(--bg-secondary)]" />
      </div>
      <div className="mt-3 h-6 w-3/4 rounded bg-[var(--bg-tertiary)]" />
      <div className="mt-2 space-y-2">
        <div className="h-4 w-full rounded bg-[var(--bg-secondary)]" />
        <div className="h-4 w-5/6 rounded bg-[var(--bg-secondary)]" />
      </div>
    </div>
  );
}

export function CaseListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <CaseCardSkeleton key={i} />
      ))}
    </div>
  );
}

export function GraphSkeleton() {
  return (
    <div className="vw-card animate-pulse rounded-xl p-5">
      <div className="h-[600px] rounded-xl bg-[var(--bg-secondary)]" />
    </div>
  );
}

export function StatCardSkeleton() {
  return (
    <div className="vw-card animate-pulse rounded-xl p-5">
      <div className="h-4 w-20 rounded bg-[var(--bg-secondary)]" />
      <div className="mt-3 h-10 w-16 rounded bg-[var(--bg-tertiary)]" />
      <div className="mt-2 h-3 w-32 rounded bg-[var(--bg-secondary)]" />
    </div>
  );
}
