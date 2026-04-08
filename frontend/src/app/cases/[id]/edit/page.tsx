"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "@/components/AppShell";
import { api, apiExtended, type Case } from "@/lib/api";

export default function EditCasePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [caseData, setCaseData] = useState<Partial<Case>>({});

  useEffect(() => {
    async function loadCase() {
      try {
        const data = await api.case(id);
        setCaseData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "加载失败");
      } finally {
        setLoading(false);
      }
    }
    loadCase();
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      await apiExtended.updateCase(id, caseData);
      router.push(`/cases/${id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field: keyof Case, value: string) => {
    setCaseData((prev) => ({ ...prev, [field]: value }));
  };

  if (loading) {
    return (
      <AppShell title="编辑案例">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="text-lg text-[var(--text-muted)]">加载中...</div>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell title="编辑案例">
      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
            案例ID
          </label>
          <input
            type="text"
            value={caseData.id || ""}
            disabled
            className="vw-input w-full bg-gray-100"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
            领域 *
          </label>
          <input
            type="text"
            value={caseData.domain || ""}
            onChange={(e) => handleChange("domain", e.target.value)}
            required
            className="vw-input w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
            标题 *
          </label>
          <input
            type="text"
            value={caseData.title || ""}
            onChange={(e) => handleChange("title", e.target.value)}
            required
            className="vw-input w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
            描述
          </label>
          <textarea
            value={caseData.description || ""}
            onChange={(e) => handleChange("description", e.target.value)}
            rows={4}
            className="vw-input w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
            决策节点
          </label>
          <textarea
            value={caseData.decision_node || ""}
            onChange={(e) => handleChange("decision_node", e.target.value)}
            rows={3}
            className="vw-input w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
            采取行动
          </label>
          <textarea
            value={caseData.action_taken || ""}
            onChange={(e) => handleChange("action_taken", e.target.value)}
            rows={3}
            className="vw-input w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
            结果
          </label>
          <textarea
            value={caseData.outcome_result || ""}
            onChange={(e) => handleChange("outcome_result", e.target.value)}
            rows={3}
            className="vw-input w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
            时间线
          </label>
          <input
            type="text"
            value={caseData.outcome_timeline || ""}
            onChange={(e) => handleChange("outcome_timeline", e.target.value)}
            className="vw-input w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
            核心教训
          </label>
          <textarea
            value={caseData.lesson_core || ""}
            onChange={(e) => handleChange("lesson_core", e.target.value)}
            rows={3}
            className="vw-input w-full"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-[var(--text-primary)] mb-2">
            置信度
          </label>
          <select
            value={caseData.confidence || ""}
            onChange={(e) => handleChange("confidence", e.target.value)}
            className="vw-input w-full"
          >
            <option value="">未设置</option>
            <option value="high">高</option>
            <option value="medium">中</option>
            <option value="low">低</option>
          </select>
        </div>

        <div className="flex gap-3 pt-4">
          <button
            type="submit"
            disabled={saving}
            className="vw-btn-primary px-6 py-2.5 text-sm font-medium"
          >
            {saving ? "保存中..." : "保存更改"}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="vw-btn-secondary px-6 py-2.5 text-sm"
          >
            取消
          </button>
        </div>
      </form>
    </AppShell>
  );
}
