"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/AppShell";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const [aiConfig, setAiConfig] = useState({
    provider: "ollama",
    model: "qwen3.5:4b",
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
    // 加载当前配置
    api.getAIConfig()
      .then((config) => {
        setAiConfig((prev) => ({
          ...prev,
          provider: config.provider || "ollama",
          model: config.model || "qwen3.5:4b",
          api_base: config.api_base || "",
        }));
      })
      .catch((e) => {
        console.error("Failed to load AI config:", e);
        // 使用默认配置
        setAiConfig((prev) => ({
          ...prev,
          provider: "ollama",
          model: "qwen3.5:4b",
        }));
      });

    // 检查AI状态
    api.getAIStatus()
      .then((status) => {
        setAiStatus(status);
      })
      .catch((e) => {
        console.error("Failed to load AI status:", e);
        // 设置为不可用
        setAiStatus({
          available: false,
          provider: "ollama",
          model: "qwen3.5:4b",
        });
      });
  }, []);

  const handleSave = async () => {
    setLoading(true);
    setMessage("");
    try {
      await api.updateAIConfig(aiConfig);
      setMessage("配置已保存");
      // 刷新状态
      const status = await api.getAIStatus();
      setAiStatus(status);
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "保存失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell title="设置">
      <div className="max-w-2xl space-y-6">
        {/* AI配置 */}
        <div className="rounded-lg border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-medium">AI 配置</h2>
            <div className="flex items-center gap-2">
              <span
                className={`h-2 w-2 rounded-full ${
                  aiStatus.available ? "bg-green-500" : "bg-red-500"
                }`}
              />
              <span className="text-xs text-[var(--text-muted)]">
                {aiStatus.available ? "服务正常" : "服务不可用"}
              </span>
            </div>
          </div>

          <div className="space-y-4">
            {/* 提供商选择 */}
            <div>
              <label className="mb-1 block text-sm text-[var(--text-muted)]">
                AI 提供商
              </label>
              <select
                value={aiConfig.provider}
                onChange={(e) =>
                  setAiConfig({ ...aiConfig, provider: e.target.value })
                }
                className="w-full rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)] outline-none focus:border-[color:var(--accent-primary)]"
              >
                <option value="ollama">本地 Ollama</option>
                <option value="api">远程 API (OpenAI格式)</option>
              </select>
            </div>

            {/* 模型 */}
            <div>
              <label className="mb-1 block text-sm text-[var(--text-muted)]">
                模型名称
              </label>
              <input
                type="text"
                value={aiConfig.model}
                onChange={(e) =>
                  setAiConfig({ ...aiConfig, model: e.target.value })
                }
                placeholder={
                  aiConfig.provider === "ollama"
                    ? "如: qwen3.5:4b, deepseek-r1:7b"
                    : "如: gpt-4, gpt-3.5-turbo"
                }
                className="w-full rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)] outline-none focus:border-[color:var(--accent-primary)]"
              />
              <p className="mt-1 text-xs text-[var(--text-muted)]">
                {aiConfig.provider === "ollama"
                  ? "使用 ollama list 查看可用模型"
                  : "填写API提供商支持的模型名称"}
              </p>
            </div>

            {/* API配置（仅在API模式下显示） */}
            {aiConfig.provider === "api" && (
              <>
                <div>
                  <label className="mb-1 block text-sm text-[var(--text-muted)]">
                    API Base URL
                  </label>
                  <input
                    type="text"
                    value={aiConfig.api_base}
                    onChange={(e) =>
                      setAiConfig({ ...aiConfig, api_base: e.target.value })
                    }
                    placeholder="https://api.openai.com/v1"
                    className="w-full rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)] outline-none focus:border-[color:var(--accent-primary)]"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm text-[var(--text-muted)]">
                    API Key
                  </label>
                  <input
                    type="password"
                    value={aiConfig.api_key}
                    onChange={(e) =>
                      setAiConfig({ ...aiConfig, api_key: e.target.value })
                    }
                    placeholder="sk-..."
                    className="w-full rounded-md border border-[color:var(--bg-tertiary)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)] outline-none focus:border-[color:var(--accent-primary)]"
                  />
                  <p className="mt-1 text-xs text-[var(--text-muted)]">
                    API密钥仅保存在本地，不会上传到服务器
                  </p>
                </div>
              </>
            )}

            {/* 保存按钮 */}
            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={handleSave}
                disabled={loading}
                className="rounded-md bg-[var(--accent-primary)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--accent-hover)] disabled:opacity-50"
              >
                {loading ? "保存中..." : "保存配置"}
              </button>
              {message && (
                <span
                  className={`text-sm ${
                    message.includes("失败") || message.includes("错误")
                      ? "text-red-400"
                      : "text-green-400"
                  }`}
                >
                  {message}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* 说明 */}
        <div className="rounded-lg border border-[color:var(--bg-tertiary)] bg-[var(--bg-secondary)] p-6">
          <h2 className="mb-4 text-lg font-medium">使用说明</h2>
          <div className="space-y-2 text-sm text-[var(--text-secondary)]">
            <p>
              <strong className="text-[var(--text-primary)]">本地 Ollama:</strong>{" "}
              需要在本地运行 Ollama 服务，支持离线使用，无需API密钥。
            </p>
            <p>
              <strong className="text-[var(--text-primary)]">远程 API:</strong>{" "}
              支持OpenAI格式的API，如OpenAI、Azure OpenAI、第三方代理等。
            </p>
            <p className="text-xs text-[var(--text-muted)]">
              配置更改后会立即生效，用于决策查询和自动分类功能。
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
