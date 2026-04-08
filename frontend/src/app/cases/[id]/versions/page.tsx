"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import { apiExtended, type CaseVersion } from "@/lib/api";

export default function CaseVersionsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [versions, setVersions] = useState<CaseVersion[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [restoring, setRestoring] = useState<number | null>(null);

  useEffect(() => {
    async function loadVersions() {
      try {
        const data = await apiExtended.getCaseVersions(id);
        setVersions(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "加载失败");
      } finally {
        setLoading(false);
      }
    }
    loadVersions();
  }, [id]);

  const handleRestore = async (versionNumber: number) => {
    if (!confirm(`确定要恢复到版本 ${versionNumber} 吗？`)) {
      return;
    }

    setRestoring(versionNumber);
    try {
      await apiExtended.restoreCaseVersion(id, versionNumber);
      router.push(`/cases/${id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "恢复失败");
    } finally {
      setRestoring(null);
    }
  };

  if (loading) {
    return (
      <AppShell title="版本历史">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="text-lg text-[var(--text-muted)]">加载中...</div>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell title="版本历史">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <Link href={`/cases/${id}`} className="text-sm text-[var(--accent-secondary)] hover:text-[var(--text-primary)]">
            返回案例详情
          </Link>
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            {error}
          </div>
        )}

        {versions.length === 0 ? (
          <div className="rounded-2xl border border-[color:var(--border-subtle)] bg-[#f8f9fa] p-8 text-center">
            <div className="text-lg font-medium text-[var(--text-primary)]">暂无版本历史</div>
            <div className="mt-2 text-sm text-[var(--text-muted)]">
              编辑案例后会自动保存版本历史
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {versions.map((version) => (
              <div
                key={version.id}
                className="vw-card rounded-[24px] p-5 flex items-center justify-between"
              >
                <div>
                  <div className="flex items-center gap-3">
                    <span className="vw-badge vw-badge-accent">
                      版本 {version.version_number}
                    </span>
                    <span className="text-sm text-[var(--text-muted)]">
                      {new Date(version.created_at).toLocaleString("zh-CN")}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Link
                    href={`/cases/${id}/versions/${version.version_number}`}
                    className="vw-btn-secondary px-4 py-2 text-sm"
                  >
                    查看
                  </Link>
                  <button
                    onClick={() => handleRestore(version.version_number)}
                    disabled={restoring === version.version_number}
                    className="vw-btn-primary px-4 py-2 text-sm font-medium"
                  >
                    {restoring === version.version_number ? "恢复中..." : "恢复"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
