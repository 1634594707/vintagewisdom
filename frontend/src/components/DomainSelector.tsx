"use client";

import { useState } from "react";
import { DOMAINS, QUICK_TAGS, type Domain, type SubDomain } from "@/lib/domains";

interface DomainSelectorProps {
  selectedDomains: string[];
  onChange: (domains: string[]) => void;
  selectedTags: string[];
  onTagsChange: (tags: string[]) => void;
  enableAutoClassify?: boolean;
  onAutoClassifyChange?: (enabled: boolean) => void;
}

export default function DomainSelector({
  selectedDomains,
  onChange,
  selectedTags,
  onTagsChange,
  enableAutoClassify = false,
  onAutoClassifyChange,
}: DomainSelectorProps) {
  const [expandedDomain, setExpandedDomain] = useState<string | null>(null);

  const toggleDomain = (code: string) => {
    if (selectedDomains.includes(code)) {
      onChange(selectedDomains.filter((d) => d !== code));
    } else {
      onChange([...selectedDomains, code]);
    }
  };

  const toggleTag = (code: string) => {
    if (selectedTags.includes(code)) {
      onTagsChange(selectedTags.filter((t) => t !== code));
    } else {
      onTagsChange([...selectedTags, code]);
    }
  };

  const selectAllSubDomains = (domain: Domain) => {
    const subCodes = domain.subDomains.map((s) => s.code);
    const hasAll = subCodes.every((code) => selectedDomains.includes(code));
    if (hasAll) {
      onChange(selectedDomains.filter((d) => !subCodes.includes(d)));
    } else {
      const newSelection = [...new Set([...selectedDomains, ...subCodes])];
      onChange(newSelection);
    }
  };

  return (
    <div className="space-y-4">
      {/* AI自动分类开关 */}
      {onAutoClassifyChange && (
        <div className="flex items-center gap-3 rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] p-3">
          <input
            type="checkbox"
            id="auto-classify"
            checked={enableAutoClassify}
            onChange={(e) => onAutoClassifyChange(e.target.checked)}
            className="h-4 w-4 rounded border-[color:var(--bg-tertiary)]"
          />
          <label htmlFor="auto-classify" className="flex-1 text-sm">
            <span className="font-medium">AI自动分类</span>
            <span className="ml-2 text-[var(--text-muted)]">
              上传后自动分析内容并推荐领域标签
            </span>
          </label>
          <span className="text-lg">🤖</span>
        </div>
      )}

      {/* 领域选择 */}
      <div className="rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-4">
        <div className="mb-3 text-sm font-medium">选择决策领域（可多选）</div>

        <div className="space-y-2">
          {DOMAINS.map((domain) => (
            <div
              key={domain.code}
              className="rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)]"
            >
              {/* 主领域标题 */}
              <button
                type="button"
                onClick={() =>
                  setExpandedDomain(
                    expandedDomain === domain.code ? null : domain.code
                  )
                }
                className="flex w-full items-center justify-between px-3 py-2 text-left hover:bg-[var(--bg-secondary)]"
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">{domain.icon}</span>
                  <span className="font-medium">{domain.name}</span>
                  <span className="text-xs text-[var(--text-muted)]">
                    {domain.nameEn}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-[var(--text-muted)]">
                    {domain.subDomains.filter((s) =>
                      selectedDomains.includes(s.code)
                    ).length > 0
                      ? `已选 ${domain.subDomains.filter((s) => selectedDomains.includes(s.code)).length} 项`
                      : ""}
                  </span>
                  <span
                    className={`text-[var(--text-muted)] transition-transform ${
                      expandedDomain === domain.code ? "rotate-180" : ""
                    }`}
                  >
                    ▼
                  </span>
                </div>
              </button>

              {/* 子领域列表 */}
              {expandedDomain === domain.code && (
                <div className="border-t border-[color:var(--bg-tertiary)] px-3 py-2">
                  <div className="mb-2 flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => selectAllSubDomains(domain)}
                      className="text-xs text-[var(--accent-primary)] hover:underline"
                    >
                      {domain.subDomains.every((s) =>
                        selectedDomains.includes(s.code)
                      )
                        ? "取消全选"
                        : "全选"}
                    </button>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {domain.subDomains.map((sub) => (
                      <label
                        key={sub.code}
                        className="flex cursor-pointer items-center gap-2 rounded-md p-2 hover:bg-[var(--bg-secondary)]"
                      >
                        <input
                          type="checkbox"
                          checked={selectedDomains.includes(sub.code)}
                          onChange={() => toggleDomain(sub.code)}
                          className="h-4 w-4 rounded border-[color:var(--bg-tertiary)]"
                        />
                        <div className="flex flex-col">
                          <span className="text-sm">{sub.name}</span>
                          <span className="text-[10px] text-[var(--text-muted)]">
                            {sub.code}
                          </span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 快速标签 */}
      <div className="rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-4">
        <div className="mb-3 text-sm font-medium">快速标签</div>
        <div className="flex flex-wrap gap-2">
          {QUICK_TAGS.map((tag) => (
            <button
              key={tag.code}
              type="button"
              onClick={() => toggleTag(tag.code)}
              className={`rounded-full px-3 py-1 text-xs transition-colors ${
                selectedTags.includes(tag.code)
                  ? "text-white"
                  : "bg-[var(--bg-primary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
              style={
                selectedTags.includes(tag.code)
                  ? { backgroundColor: tag.color }
                  : {}
              }
            >
              {selectedTags.includes(tag.code) ? "✓ " : ""}
              {tag.name}
            </button>
          ))}
        </div>
      </div>

      {/* 已选摘要 */}
      {(selectedDomains.length > 0 || selectedTags.length > 0) && (
        <div className="rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] p-3">
          <div className="mb-2 text-xs text-[var(--text-muted)]">已选择</div>
          <div className="flex flex-wrap gap-1">
            {selectedDomains.map((code) => {
              const domain = DOMAINS.find((d) =>
                d.subDomains.some((s) => s.code === code)
              );
              const subDomain = domain?.subDomains.find((s) => s.code === code);
              return (
                <span
                  key={code}
                  className="inline-flex items-center gap-1 rounded-full bg-[var(--accent-primary)] px-2 py-0.5 text-xs text-white"
                >
                  {domain?.icon} {subDomain?.name}
                  <button
                    type="button"
                    onClick={() => toggleDomain(code)}
                    className="ml-1 hover:text-red-200"
                  >
                    ×
                  </button>
                </span>
              );
            })}
            {selectedTags.map((code) => {
              const tag = QUICK_TAGS.find((t) => t.code === code);
              return (
                <span
                  key={code}
                  className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs text-white"
                  style={{ backgroundColor: tag?.color }}
                >
                  {tag?.name}
                  <button
                    type="button"
                    onClick={() => toggleTag(code)}
                    className="ml-1 hover:opacity-70"
                  >
                    ×
                  </button>
                </span>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
