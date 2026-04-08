"use client";

import { useState } from "react";
import AppShell from "@/components/AppShell";
import { apiExtended } from "@/lib/api";

type ExportType = "cases" | "decisions" | "graph";
type ExportFormat = "json" | "csv" | "markdown";

export default function ExportPage() {
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleExport = async (type: ExportType, format: ExportFormat) => {
    setExporting(true);
    setError(null);
    setSuccess(null);

    try {
      let result;
      if (type === "cases") {
        result = await apiExtended.exportCases({ format });
      } else if (type === "decisions") {
        result = await apiExtended.exportDecisions(format === "markdown" ? "markdown" : "json");
      } else {
        result = await apiExtended.exportGraph();
      }

      // 创建下载链接
      const blob = new Blob(
        [typeof result.data === "string" ? result.data : JSON.stringify(result.data ?? {}, null, 2)],
        { type: format === "json" ? "application/json" : format === "csv" ? "text/csv" : "text/markdown" }
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `vintagewisdom_${type}_${new Date().toISOString().split("T")[0]}.${format === "markdown" ? "md" : format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setSuccess(`成功导出 ${result.count || 0} 条记录`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "导出失败");
    } finally {
      setExporting(false);
    }
  };

  return (
    <AppShell title="数据导出">
      <div className="space-y-6">
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            {error}
          </div>
        )}

        {success && (
          <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-800">
            {success}
          </div>
        )}

        <div className="vw-card rounded-[24px] p-6">
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">导出案例数据</h3>
          <p className="text-sm text-[var(--text-muted)] mb-4">
            导出所有案例数据，包括标题、描述、决策节点、行动和结果等完整信息。
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleExport("cases", "json")}
              disabled={exporting}
              className="vw-btn-primary px-4 py-2 text-sm font-medium"
            >
              导出为 JSON
            </button>
            <button
              onClick={() => handleExport("cases", "csv")}
              disabled={exporting}
              className="vw-btn-secondary px-4 py-2 text-sm"
            >
              导出为 CSV
            </button>
            <button
              onClick={() => handleExport("cases", "markdown")}
              disabled={exporting}
              className="vw-btn-secondary px-4 py-2 text-sm"
            >
              导出为 Markdown
            </button>
          </div>
        </div>

        <div className="vw-card rounded-[24px] p-6">
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">导出决策历史</h3>
          <p className="text-sm text-[var(--text-muted)] mb-4">
            导出所有决策查询记录，包括查询内容、推荐案例、用户决策和实际结果。
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleExport("decisions", "json")}
              disabled={exporting}
              className="vw-btn-primary px-4 py-2 text-sm font-medium"
            >
              导出为 JSON
            </button>
            <button
              onClick={() => handleExport("decisions", "markdown")}
              disabled={exporting}
              className="vw-btn-secondary px-4 py-2 text-sm"
            >
              导出为 Markdown
            </button>
          </div>
        </div>

        <div className="vw-card rounded-[24px] p-6">
          <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">导出知识图谱</h3>
          <p className="text-sm text-[var(--text-muted)] mb-4">
            导出完整的知识图谱数据，包括所有节点、边和聚类信息。
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleExport("graph", "json")}
              disabled={exporting}
              className="vw-btn-primary px-4 py-2 text-sm font-medium"
            >
              导出为 JSON
            </button>
          </div>
        </div>

        <div className="rounded-2xl border border-[color:var(--border-subtle)] bg-[#f8f9fa] p-6">
          <h4 className="text-sm font-semibold text-[var(--text-primary)] mb-2">导出说明</h4>
          <ul className="space-y-2 text-sm text-[var(--text-muted)]">
            <li>• JSON 格式适合程序处理和数据迁移</li>
            <li>• CSV 格式适合在 Excel 等表格软件中查看</li>
            <li>• Markdown 格式适合阅读和文档归档</li>
            <li>• 导出的文件会自动下载到浏览器默认下载目录</li>
            <li>• 导出时间会记录在文件中，便于追溯数据版本</li>
          </ul>
        </div>
      </div>
    </AppShell>
  );
}
