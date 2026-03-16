"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function AppShell({
  title,
  variant = "default",
  children,
}: {
  title: string;
  variant?: "default" | "canvas";
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="min-h-dvh bg-[var(--bg-primary)] text-[var(--text-primary)]">
      <header className="sticky top-0 z-50 border-b border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)]">
        <div className="mx-auto flex h-14 max-w-[1440px] items-center justify-between gap-4 px-6">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-sm font-semibold tracking-wide">
              VintageWisdom
            </Link>
            <div className="hidden text-xs text-[var(--text-muted)] md:block">{title}</div>
          </div>

          <nav className="hidden items-center gap-1 md:flex">
            <TopNavItem pathname={pathname} href="/" label="仪表盘" />
            <TopNavItem pathname={pathname} href="/import" label="导入" />
            <TopNavItem pathname={pathname} href="/cases" label="案例库" />
            <TopNavItem pathname={pathname} href="/query" label="决策查询" />
            <TopNavItem pathname={pathname} href="/graph" label="知识图谱" />
            <TopNavItem pathname={pathname} href="/settings" label="设置" />
          </nav>

          <div className="text-[11px] text-[var(--text-muted)]">
            API: {process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000"}
          </div>
        </div>
      </header>

      {variant === "canvas" ? (
        <main className="w-full px-0 py-0">{children}</main>
      ) : (
        <main className="mx-auto w-full max-w-[1440px] px-6 py-6">
          <div className="rounded-xl border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] shadow-[0_1px_0_rgba(15,23,42,0.02)]">
            <div className="p-5">{children}</div>
          </div>
        </main>
      )}
    </div>
  );
}

function TopNavItem({
  pathname,
  href,
  label,
}: {
  pathname: string;
  href: string;
  label: string;
}) {
  const active = pathname === href || (href !== "/" && pathname.startsWith(href));
  return (
    <Link
      href={href}
      className={
        active
          ? "rounded-md bg-[rgba(37,99,235,0.10)] px-3 py-1.5 text-sm text-[var(--accent-primary)]"
          : "rounded-md px-3 py-1.5 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)] hover:text-[var(--text-primary)]"
      }
    >
      {label}
    </Link>
  );
}
