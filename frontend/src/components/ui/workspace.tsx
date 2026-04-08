import type { ReactNode } from "react";

function cx(...values: Array<string | false | null | undefined>) {
  return values.filter(Boolean).join(" ");
}

export function SectionIntro({
  eyebrow,
  title,
  description,
  actions,
  aside,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  actions?: ReactNode;
  aside?: ReactNode;
}) {
  return (
    <section className="vw-panel rounded-[28px] p-5 md:p-6">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0">
          <div className="vw-eyebrow">{eyebrow}</div>
          <h2 className="vw-title mt-1 text-3xl font-semibold">{title}</h2>
          {description ? (
            <p className="mt-2 max-w-3xl text-sm leading-6 text-[var(--text-muted)]">{description}</p>
          ) : null}
        </div>

        {actions || aside ? (
          <div className="flex w-full max-w-full flex-col gap-3 lg:w-auto lg:items-end">
            {actions}
            {aside}
          </div>
        ) : null}
      </div>
    </section>
  );
}

export function PanelBlock({
  eyebrow,
  title,
  description,
  children,
  className,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={cx("vw-card rounded-[24px] p-5", className)}>
      <div className="vw-eyebrow">{eyebrow}</div>
      <h3 className="vw-title mt-1 text-xl font-semibold">{title}</h3>
      {description ? <p className="mt-2 text-sm leading-6 text-[var(--text-muted)]">{description}</p> : null}
      <div className="mt-4">{children}</div>
    </section>
  );
}

export function MetricCard({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: string | number;
  hint: string;
  accent?: string;
}) {
  return (
    <div className="vw-card rounded-[24px] p-5">
      <div className="vw-eyebrow">{label}</div>
      <div className="mt-3 text-3xl font-semibold text-[var(--text-primary)]" style={accent ? { color: accent } : undefined}>
        {value}
      </div>
      <div className="mt-2 text-sm text-[var(--text-muted)]">{hint}</div>
    </div>
  );
}

export function NoticeBanner({
  tone = "info",
  children,
}: {
  tone?: "info" | "success" | "warning" | "error";
  children: ReactNode;
}) {
  const styles = {
    info: "border-[color:var(--info)] bg-[var(--info-light)] text-[var(--info)]",
    success: "border-[color:var(--success)] bg-[var(--success-light)] text-[var(--success)]",
    warning: "border-[color:var(--warning)] bg-[var(--warning-light)] text-[var(--warning)]",
    error: "border-[color:var(--error)] bg-[var(--error-light)] text-[var(--error)]",
  }[tone];

  return <div className={cx("rounded-xl border px-4 py-3 text-sm", styles)}>{children}</div>;
}

export function ToggleChip({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        active
          ? "rounded-full border border-[color:var(--accent-primary)] bg-[var(--accent-light)] px-4 py-2 text-sm font-medium text-[var(--accent-primary)]"
          : "rounded-full border border-[color:var(--border-subtle)] bg-white px-4 py-2 text-sm text-[var(--text-secondary)] hover:border-[color:var(--accent-primary)] hover:text-[var(--accent-primary)]"
      }
    >
      {label}
    </button>
  );
}

export function FieldGroup({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <label className="block">
      <div className="mb-2 text-sm font-medium text-[var(--text-primary)]">{label}</div>
      {children}
      {hint ? <div className="mt-2 text-xs text-[var(--text-muted)]">{hint}</div> : null}
    </label>
  );
}

export function EmptyState({
  title,
  hint,
}: {
  title: string;
  hint: string;
}) {
  return (
    <div className="rounded-xl border border-dashed border-[color:var(--border-strong)] bg-[var(--bg-tertiary)] p-8 text-center">
      <div className="text-lg font-medium text-[var(--text-primary)]">{title}</div>
      <div className="mt-2 text-sm text-[var(--text-muted)]">{hint}</div>
    </div>
  );
}
