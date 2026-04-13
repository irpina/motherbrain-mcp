"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Key, Eye, EyeOff, Trash2, Save, Loader2 } from "lucide-react";

interface CredentialFormProps {
  agentType: string;
  agentName: string;
  hasCredential: boolean;
  onSaved: () => void;
}

function CredentialForm({ agentType, agentName, hasCredential, onSaved }: CredentialFormProps) {
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!apiKey.trim()) return;
    setIsSaving(true);
    try {
      await api.storeAgentCredential(agentType, apiKey.trim());
      setApiKey("");
      onSaved();
    } catch (err: unknown) {
      alert(`Failed to save: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Remove credentials for ${agentName}?`)) return;
    setIsDeleting(true);
    try {
      const res = await api.deleteAgentCredential(agentType);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      onSaved();
    } catch (err: unknown) {
      alert(`Failed to remove: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center gap-2 mb-3">
        <Key size={18} className="text-slate-400" />
        <h3 className="font-medium">{agentName}</h3>
        {hasCredential && (
          <span className="ml-auto text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded">
            Configured
          </span>
        )}
      </div>

      <form onSubmit={handleSave} className="space-y-3">
        <div className="relative">
          <input
            type={showKey ? "text" : "password"}
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder={hasCredential ? "Enter new API key to update" : "Enter API key"}
            className="w-full px-3 py-2 border rounded-md pr-10"
          />
          <button
            type="button"
            onClick={() => setShowKey(!showKey)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
          >
            {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={!apiKey.trim() || isSaving}
            className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isSaving && <Loader2 size={14} className="animate-spin" />}
            <Save size={14} />
            {hasCredential ? "Update" : "Save"}
          </button>
          {hasCredential && (
            <button
              type="button"
              onClick={handleDelete}
              disabled={isDeleting}
              className="px-3 py-2 border border-red-200 text-red-600 rounded-md hover:bg-red-50 disabled:opacity-50 flex items-center gap-2"
            >
              <Trash2 size={14} />
              Remove
            </button>
          )}
        </div>
      </form>
    </div>
  );
}

export default function SettingsPage() {
  const { data: credentials, isLoading } = useQuery({
    queryKey: ["agents", "credentials"],
    queryFn: api.listAgentCredentials,
  });
  const queryClient = useQueryClient();

  const hasCred = (type: string) =>
    credentials?.some((c: any) => c.agent_type === type);

  const agentTypes = [
    { type: "claude", name: "Claude Code (Anthropic)" },
    { type: "codex", name: "OpenAI Codex" },
  ];

  if (isLoading) {
    return <div className="p-6">Loading...</div>;
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Settings</h1>
      <p className="text-slate-500 mb-6">
        Configure agent credentials and system settings
      </p>

      <div className="space-y-6">
        {/* Agent Credentials */}
        <section>
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Key size={20} />
            Agent API Keys
          </h2>
          <p className="text-sm text-slate-500 mb-4">
            Store API keys for spawning agents. Keys are encrypted at rest.
          </p>

          <div className="grid gap-4 md:grid-cols-2">
            {agentTypes.map((agent) => (
              <CredentialForm
                key={agent.type}
                agentType={agent.type}
                agentName={agent.name}
                hasCredential={hasCred(agent.type)}
                onSaved={() =>
                  queryClient.invalidateQueries({ queryKey: ["agents", "credentials"] })
                }
              />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
