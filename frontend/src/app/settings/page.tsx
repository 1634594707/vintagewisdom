"use client";

import { useEffect, useState } from "react";

import AppShell from "@/components/AppShell";
import { FieldGroup, MetricCard, NoticeBanner, PanelBlock, SectionIntro } from "@/components/ui/workspace";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const [aiConfig, setAiConfig] = useState({
    provider: "api",
    model: "gpt-4.1-mini",
    api_base: "",
    api_key: "",
  });
  const [aiStatus, setAiStatus] = useState({
    available: false,
    provider: "",
    model: "",
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    api.getAIConfig().then((config) => {
      setAiConfig((prev) => ({
        ...prev,
        provider: "api",
        model: config.model || "gpt-4.1-mini",
        api_base: config.api_base || "",
      }));
    }).catch((e) => console.error("Failed to load AI config:", e));

    api.getAIStatus().then((status) => {
      setAiStatus(status);
    }).catch((e) => {
      console.error("Failed to load AI status:", e);
      setAiStatus({ available: false, provider: "api", model: "gpt-4.1-mini" });
    });
  }, []);

  const handleSave = async () => {
    setLoading(true);
    setMessage("");
    try {
      await api.updateAIConfig(aiConfig);
      setMessage("配置已保存。");
      const status = await api.getAIStatus();
      setAiStatus(status);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "保存失败。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell title="系统设置">
      <div className="space-y-4">
        <SectionIntro
          eyebrow="AI 运行层"
          title="模型与服务连通性"
          description="统一管理查询、自动分类和推理链路所使用的模型运行时，让整套判断系统保持稳定和可验证。"
          aside={
            <div className={`rounded-full px-4 py-2 text-sm ${aiStatus.available ? "border border-[color:rgba(34,197,94,0.28)] bg-[rgba(34,197,94,0.12)] text-[var(--success)]" : "border border-[color:rgba(239,68,68,0.28)] bg-[rgba(239,68,68,0.12)] text-[var(--error)]"}`}>
              {aiStatus.available ? "服务在线" : "服务离线"}
            </div>
          }
        />

        <section className="grid gap-4 md:grid-cols-3">
          <MetricCard label="当前提供方" value={aiStatus.provider || aiConfig.provider} hint="正在使用的执行后端" />
          <MetricCard label="默认模型" value={aiStatus.model || aiConfig.model} hint="当前主模型目标" />
          <MetricCard label="连通状态" value={aiStatus.available ? "在线" : "离线"} hint="实时可用性" accent={aiStatus.available ? "var(--success)" : "var(--error)"} />
        </section>

        {message ? (
          <NoticeBanner tone={message.includes("失败") || message.toLowerCase().includes("error") ? "error" : "success"}>
            {message}
          </NoticeBanner>
        ) : null}

        <section className="grid gap-4 xl:grid-cols-[1fr_0.8fr]">
          <PanelBlock eyebrow="配置面板" title="AI 提供方设置">
            <div className="space-y-4">
              <FieldGroup label="提供方">
                <input type="text" value="远程 API" disabled className="vw-input h-11 rounded-2xl px-4 text-sm opacity-70" />
              </FieldGroup>

              <FieldGroup label="模型名称" hint="例如：gpt-4.1、gpt-4o-mini">
                <input type="text" value={aiConfig.model} onChange={(e) => setAiConfig({ ...aiConfig, model: e.target.value })} className="vw-input h-11 rounded-2xl px-4 text-sm" />
              </FieldGroup>

              <FieldGroup label="API Base URL" hint="例如：https://api.openai.com/v1">
                <input type="text" value={aiConfig.api_base} onChange={(e) => setAiConfig({ ...aiConfig, api_base: e.target.value })} className="vw-input h-11 rounded-2xl px-4 text-sm" />
              </FieldGroup>
              <FieldGroup label="API Key" hint="仅用于服务端配置保存，不会在页面回显。">
                <input type="password" value={aiConfig.api_key} onChange={(e) => setAiConfig({ ...aiConfig, api_key: e.target.value })} placeholder="sk-..." className="vw-input h-11 rounded-2xl px-4 text-sm" />
              </FieldGroup>

              <div className="flex flex-wrap items-center gap-3 pt-2">
                <button type="button" onClick={handleSave} disabled={loading} className="vw-btn-primary px-5 py-2.5 text-sm font-medium disabled:opacity-60">
                  {loading ? "保存中..." : "保存配置"}
                </button>
              </div>
            </div>
          </PanelBlock>

          <div className="space-y-4">
            <PanelBlock eyebrow="运行状态" title="服务健康度">
              <div className="mt-4 space-y-3">
                <StatusRow label="提供方" value={aiStatus.provider || aiConfig.provider} />
                <StatusRow label="模型" value={aiStatus.model || aiConfig.model} />
                <StatusRow label="可用性" value={aiStatus.available ? "在线" : "离线"} />
              </div>
            </PanelBlock>

            <PanelBlock eyebrow="操作提示" title="使用建议">
              <div className="mt-4 space-y-3 text-sm leading-6 text-[var(--text-secondary)]">
                <NoteItem title="远程 API" description="线上部署建议固定使用托管模型服务，确保 Base URL 与凭证正确。" />
                <NoteItem title="即时生效" description="保存后，新发起的查询和自动分类任务会立刻使用最新配置。" />
              </div>
            </PanelBlock>
          </div>
        </section>
      </div>
    </AppShell>
  );
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-[color:var(--border-subtle)] bg-[#f8f9fa] px-4 py-3">
      <span className="text-sm text-[var(--text-muted)]">{label}</span>
      <span className="vw-mono text-sm text-[var(--text-secondary)]">{value}</span>
    </div>
  );
}

function NoteItem({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-2xl border border-[color:var(--border-subtle)] bg-[#f8f9fa] p-4">
      <div className="font-medium text-[var(--text-primary)]">{title}</div>
      <div className="mt-1 text-sm text-[var(--text-muted)]">{description}</div>
    </div>
  );
}
