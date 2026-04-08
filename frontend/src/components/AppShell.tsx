"use client";

import type { ReactNode } from "react";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "总览", shortLabel: "总览", index: "01" },
  { href: "/cases", label: "案例库", shortLabel: "案例", index: "02" },
  { href: "/query", label: "决策查询", shortLabel: "查询", index: "03" },
  { href: "/decisions", label: "决策历史", shortLabel: "历史", index: "04" },
  { href: "/import", label: "导入中心", shortLabel: "导入", index: "05" },
  { href: "/graph", label: "知识图谱", shortLabel: "图谱", index: "06" },
  { href: "/settings", label: "系统设置", shortLabel: "设置", index: "07" },
];

const PAGE_META: Record<string, { section: string; subtitle: string }> = {
  "/": {
    section: "决策驾驶舱",
    subtitle: "把历史案例、实时判断和行动建议放进同一个工作台，让经验真正变成可复用资产。",
  },
  "/cases": {
    section: "案例档案库",
    subtitle: "按标题、领域、经验教训和时间线快速扫描案例，像查阅一套可搜索的判断档案。",
  },
  "/query": {
    section: "决策查询台",
    subtitle: "描述当前处境，系统会回忆相似案例、整理推理线索，并给出可执行建议。",
  },
  "/decisions": {
    section: "决策历史库",
    subtitle: "回顾过去的决策查询、推荐结果和实际反馈，持续改进决策质量。",
  },
  "/import": {
    section: "材料入库台",
    subtitle: "把 CSV、JSON、PDF 与 Word 材料导入知识底座，并补齐领域标签与任务进度。",
  },
  "/graph": {
    section: "关系画布",
    subtitle: "从图谱视角查看案例、实体、聚类与关系链，理解结构而不是只读条目。",
  },
  "/settings": {
    section: "运行控制室",
    subtitle: "统一管理本地模型、远程接口和 AI 运行状态，让整套判断链路保持稳定。",
  },
};

export default function AppShell({
  title,
  variant = "default",
  children,
}: {
  title: string;
  variant?: "default" | "canvas";
  children: ReactNode;
}) {
  const pathname = usePathname();
  const apiBase = process.env.NEXT_PUBLIC_API_BASE || "/api";
  const meta =
    PAGE_META[pathname] ||
    (pathname.startsWith("/cases/")
      ? {
          section: "案例细读",
          subtitle: "拆开单个案例的决策节点、执行动作、结果链条和可迁移经验。",
        }
      : PAGE_META["/"]);

  return (
    <div className="min-h-dvh bg-[var(--bg-secondary)] text-[var(--text-primary)]">
      <div className="mx-auto flex min-h-dvh w-full max-w-[1680px] gap-4 px-3 py-3 lg:gap-6 lg:px-6 lg:py-5">
        <aside className="vw-panel hidden w-[272px] shrink-0 overflow-hidden rounded-2xl lg:flex lg:flex-col">
          <div className="border-b border-[color:var(--border-subtle)] px-5 py-6">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--accent-primary)] to-[var(--accent-secondary)] text-base font-bold text-white shadow-lg">
                VW
              </div>
              <div>
                <div className="vw-title text-2xl font-bold">VintageWisdom</div>
                <div className="text-xs text-[var(--text-muted)]">决策支持系统</div>
              </div>
            </div>
          </div>

          <div className="flex-1 px-4 py-5">
            <div className="vw-eyebrow mb-3 px-2">工作区导航</div>
            <nav className="space-y-1.5" aria-label="主导航">
              {NAV_ITEMS.map((item) => (
                <SidebarNavItem
                  key={item.href}
                  pathname={pathname}
                  href={item.href}
                  label={item.label}
                  index={item.index}
                />
              ))}
            </nav>
          </div>

          <div className="border-t border-[color:var(--border-subtle)] px-4 py-5">
            <div className="rounded-xl border border-[color:var(--border-subtle)] bg-[var(--bg-secondary)] p-4">
              <div className="vw-eyebrow">当前页面</div>
              <div className="mt-2 text-base font-medium text-[var(--text-primary)]">{title}</div>
              <div className="mt-3 rounded-lg border border-[color:var(--border-subtle)] bg-white p-3">
                <div className="text-[11px] text-[var(--text-muted)]">API 端点</div>
                <div className="vw-mono mt-1 break-all text-xs text-[var(--text-secondary)]">{apiBase}</div>
              </div>
            </div>
          </div>
        </aside>

        <div className="min-w-0 flex-1">
          <header className="vw-panel rounded-2xl px-4 py-4 md:px-5">
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                <div className="min-w-0">
                  <div className="vw-eyebrow">{meta.section}</div>
                  <h1 className="vw-title mt-2 text-4xl font-bold md:text-5xl">{title}</h1>
                  <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--text-muted)]">{meta.subtitle}</p>
                </div>

                <div className="flex flex-col gap-3 xl:items-end">
                  <div className="flex flex-wrap items-center gap-2">
                    <Link href="/query" className="vw-btn-primary px-4 py-2 text-sm font-medium">
                      发起查询
                    </Link>
                    <Link href="/cases" className="vw-btn-secondary px-4 py-2 text-sm">
                      查看案例
                    </Link>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <span className="vw-badge vw-badge-accent">本地优先</span>
                    <span className="vw-badge vw-badge-success">键盘友好</span>
                  </div>
                </div>
              </div>

              <div className="flex gap-2 overflow-x-auto pb-1 lg:hidden">
                {NAV_ITEMS.map((item) => (
                  <TopNavItem
                    key={item.href}
                    pathname={pathname}
                    href={item.href}
                    label={item.shortLabel}
                  />
                ))}
              </div>
            </div>
          </header>

          <main className={variant === "canvas" ? "pt-4" : "pt-4 lg:pt-5"}>
            {variant === "canvas" ? (
              children
            ) : (
              <div className="rounded-2xl border border-[color:var(--border-subtle)] bg-white p-3 md:p-4 lg:p-5">
                {children}
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}

function SidebarNavItem({
  pathname,
  href,
  label,
  index,
}: {
  pathname: string;
  href: string;
  label: string;
  index: string;
}) {
  const active = pathname === href || (href !== "/" && pathname.startsWith(href));

  return (
    <Link
      href={href}
      className={
        active
          ? "flex items-center justify-between rounded-lg border border-[color:var(--accent-primary)] bg-[var(--accent-light)] px-3 py-3 text-sm font-medium text-[var(--accent-primary)]"
          : "flex items-center justify-between rounded-lg border border-transparent px-3 py-3 text-sm text-[var(--text-secondary)] hover:border-[color:var(--border-subtle)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]"
      }
    >
      <span>{label}</span>
      <span className="vw-mono text-[11px] text-[var(--text-disabled)]">{index}</span>
    </Link>
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
          ? "rounded-full border border-[color:var(--accent-primary)] bg-[var(--accent-light)] px-3 py-1.5 text-sm font-medium text-[var(--accent-primary)]"
          : "rounded-full border border-[color:var(--border-subtle)] bg-white px-3 py-1.5 text-sm text-[var(--text-secondary)] hover:border-[color:var(--accent-primary)] hover:text-[var(--accent-primary)]"
      }
    >
      {label}
    </Link>
  );
}
