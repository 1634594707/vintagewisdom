"use client";

import { useState } from "react";

import { DOMAINS, QUICK_TAGS, type Domain } from "@/lib/domains";

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
      return;
    }
    onChange([...selectedDomains, code]);
  };

  const toggleTag = (code: string) => {
    if (selectedTags.includes(code)) {
      onTagsChange(selectedTags.filter((t) => t !== code));
      return;
    }
    onTagsChange([...selectedTags, code]);
  };

  const selectAllSubDomains = (domain: Domain) => {
    const subCodes = domain.subDomains.map((s) => s.code);
    const hasAll = subCodes.every((code) => selectedDomains.includes(code));
    if (hasAll) {
      onChange(selectedDomains.filter((d) => !subCodes.includes(d)));
      return;
    }
    onChange([...new Set([...selectedDomains, ...subCodes])]);
  };

  return (
    <div className="space-y-4">
      {onAutoClassifyChange ? (
        <div className="rounded-[24px] border border-[color:var(--border-subtle)] bg-[#f8f9fa] p-4">
          <label htmlFor="auto-classify" className="flex cursor-pointer items-start gap-3">
            <input
              type="checkbox"
              id="auto-classify"
              checked={enableAutoClassify}
              onChange={(e) => onAutoClassifyChange(e.target.checked)}
              className="mt-1 h-4 w-4 rounded border-[color:var(--border-subtle)] bg-transparent"
            />
            <div className="flex-1">
              <div className="text-sm font-medium text-[var(--text-primary)]">启用 AI 自动分类</div>
              <div className="mt-1 text-sm leading-6 text-[var(--text-muted)]">
                上传后自动分析内容，补充更可能的领域标签与主题方向，减少手工整理成本。
              </div>
            </div>
            <div className="rounded-full bg-[rgba(99,102,241,0.12)] px-2.5 py-1 text-xs text-[var(--accent-primary)]">
              AI
            </div>
          </label>
        </div>
      ) : null}

      <div className="rounded-[24px] border border-[color:var(--border-subtle)] bg-[#f8f9fa] p-4">
        <div className="mb-3">
          <div className="text-sm font-medium text-[var(--text-primary)]">选择决策领域</div>
          <div className="mt-1 text-xs text-[var(--text-muted)]">支持多选，可先展开一级领域，再勾选具体子类。</div>
        </div>

        <div className="space-y-2">
          {DOMAINS.map((domain) => {
            const selectedCount = domain.subDomains.filter((s) => selectedDomains.includes(s.code)).length;
            const allSelected = selectedCount === domain.subDomains.length;

            return (
              <div
                key={domain.code}
                className="rounded-2xl border border-[color:var(--border-subtle)] bg-white"
              >
                <button
                  type="button"
                  onClick={() => setExpandedDomain(expandedDomain === domain.code ? null : domain.code)}
                  className="flex w-full items-center justify-between px-4 py-3 text-left"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-lg">{domain.icon}</span>
                    <div>
                      <div className="text-sm font-medium text-[var(--text-primary)]">{domain.name}</div>
                      <div className="text-[11px] text-[var(--text-muted)]">{domain.nameEn}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-[var(--text-muted)]">
                      {selectedCount > 0 ? `已选 ${selectedCount} 项` : "未选择"}
                    </span>
                    <span
                      className={`text-sm text-[var(--text-muted)] transition-transform ${
                        expandedDomain === domain.code ? "rotate-180" : ""
                      }`}
                    >
                      ▾
                    </span>
                  </div>
                </button>

                {expandedDomain === domain.code ? (
                  <div className="border-t border-[color:var(--border-subtle)] px-4 py-3">
                    <button
                      type="button"
                      onClick={() => selectAllSubDomains(domain)}
                      className="mb-3 text-xs text-[var(--accent-secondary)] hover:text-[var(--text-primary)]"
                    >
                      {allSelected ? "取消该领域全选" : "全选该领域"}
                    </button>
                    <div className="grid gap-2 md:grid-cols-2">
                      {domain.subDomains.map((sub) => (
                        <label
                          key={sub.code}
                          className="flex cursor-pointer items-center gap-3 rounded-2xl border border-[color:var(--border-subtle)] bg-[#f8f9fa] px-3 py-3"
                        >
                          <input
                            type="checkbox"
                            checked={selectedDomains.includes(sub.code)}
                            onChange={() => toggleDomain(sub.code)}
                            className="h-4 w-4 rounded border-[color:var(--border-subtle)] bg-transparent"
                          />
                          <div>
                            <div className="text-sm text-[var(--text-primary)]">{sub.name}</div>
                            <div className="vw-mono text-[11px] text-[var(--text-muted)]">{sub.code}</div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      </div>

      <div className="rounded-[24px] border border-[color:var(--border-subtle)] bg-[#f8f9fa] p-4">
        <div className="mb-3">
          <div className="text-sm font-medium text-[var(--text-primary)]">快捷标签</div>
          <div className="mt-1 text-xs text-[var(--text-muted)]">用于补充风险、时效、可逆性和多方博弈等判断维度。</div>
        </div>
        <div className="flex flex-wrap gap-2">
          {QUICK_TAGS.map((tag) => (
            <button
              key={tag.code}
              type="button"
              onClick={() => toggleTag(tag.code)}
              className={`rounded-full px-3 py-1.5 text-xs ${
                selectedTags.includes(tag.code)
                  ? "text-white"
                  : "border border-[color:var(--border-subtle)] bg-white text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
              style={selectedTags.includes(tag.code) ? { backgroundColor: tag.color } : undefined}
            >
              {selectedTags.includes(tag.code) ? "已选 · " : ""}
              {tag.name}
            </button>
          ))}
        </div>
      </div>

      {selectedDomains.length > 0 || selectedTags.length > 0 ? (
        <div className="rounded-[24px] border border-[color:var(--border-subtle)] bg-[#f8f9fa] p-4">
          <div className="text-xs uppercase tracking-[0.18em] text-[var(--text-disabled)]">当前选择</div>
          <div className="mt-3 flex flex-wrap gap-2">
            {selectedDomains.map((code) => {
              const domain = DOMAINS.find((d) => d.subDomains.some((s) => s.code === code));
              const subDomain = domain?.subDomains.find((s) => s.code === code);
              return (
                <button
                  key={code}
                  type="button"
                  onClick={() => toggleDomain(code)}
                  className="inline-flex items-center gap-2 rounded-full bg-[var(--accent-primary)] px-3 py-1.5 text-xs text-[#140f0b]"
                >
                  <span>{domain?.icon}</span>
                  <span>{subDomain?.name ?? code}</span>
                  <span>×</span>
                </button>
              );
            })}
            {selectedTags.map((code) => {
              const tag = QUICK_TAGS.find((t) => t.code === code);
              return (
                <button
                  key={code}
                  type="button"
                  onClick={() => toggleTag(code)}
                  className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs text-white"
                  style={{ backgroundColor: tag?.color }}
                >
                  <span>{tag?.name ?? code}</span>
                  <span>×</span>
                </button>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
}
