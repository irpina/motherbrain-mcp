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
      console.error(`Failed to save: ${err instanceof Error ? err.message : String(err)}`);
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
      console.error(`Failed to remove: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="border border-border rounded-lg p-4 bg-elevated">
      <div className="flex items-center gap-2 mb-3">
        <Key size={18} className="text-muted-foreground" />
        <h3 className="font-medium">{agentName}</h3>
        {hasCredential && (
          <span className="ml-auto text-xs bg-success-dim text-success border border-success/20 px-2 py-0.5 rounded">
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
            className="w-full px-3 py-2 bg-input border border-border rounded-md pr-10 text-primary placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent/50"
          />
          <button
            type="button"
            onClick={() => setShowKey(!showKey)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-muted-foreground"
          >
            {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        </div>

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={!apiKey.trim() || isSaving}
            className="flex-1 px-3 py-2 bg-accent text-white rounded-md hover:bg-accent-hover disabled:opacity-50 flex items-center justify-center gap-2"
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
              className="px-3 py-2 border border-destructive/20 text-destructive rounded-md hover:bg-destructive-dim disabled:opacity-50 flex items-center gap-2"
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
    credentials?.some((c: any) => c.agent_type === type) ?? false;

  const agentTypes = [
    { type: "claude", name: "Claude Code (Anthropic)" },
    { type: "codex", name: "OpenAI Codex" },
    { type: "kimi", name: "Kimi Code (Moonshot AI)" },
  ];

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center text-muted-foreground gap-2">
        <Loader2 className="w-4 h-4 animate-spin" />
        Loading...
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-medium mb-2">Settings</h1>
      <p className="text-muted-foreground mb-6">
        Configure agent credentials and system settings
      </p>

      <div className="space-y-6">
        {/* Agent Credentials */}
        <section>
          <h2 className="text-lg font-medium mb-4 flex items-center gap-2">
            <Key size={20} />
            Agent API Keys
          </h2>
          <p className="text-sm text-muted-foreground mb-4">
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
