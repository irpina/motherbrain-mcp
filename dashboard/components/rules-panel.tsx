"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ScrollText, CheckCircle, Archive, RotateCcw, Trash2, Plus, Shield, Loader2 } from "lucide-react";

const statusBadgeColors: Record<string, string> = {
  pending: "bg-warning-dim text-warning border border-warning/20",
  active: "bg-success-dim text-success border border-success/20",
  archived: "bg-subtle text-muted-foreground border border-border",
  draft: "bg-blue-900/40 text-blue-300 border border-blue-800/50",
};

export function RulesPanel() {
  const queryClient = useQueryClient();
  const [filterStatus, setFilterStatus] = useState("");
  const [showNewRule, setShowNewRule] = useState(false);
  const [newRuleText, setNewRuleText] = useState("");
  const [newRuleReason, setNewRuleReason] = useState("");

  const { data: rulesData, isLoading } = useQuery({
    queryKey: ["rules", filterStatus],
    queryFn: () => api.listRules({ status: filterStatus || undefined, limit: 100 }),
    refetchInterval: 15000,
  });

  const { data: activeRulesData } = useQuery({
    queryKey: ["rules", "active"],
    queryFn: () => api.getActiveRules(),
    refetchInterval: 15000,
  });

  const rules = rulesData?.rules || [];
  const activeCount = activeRulesData?.count || 0;
  const epoch = activeRulesData?.epoch || 0;

  const handleActivate = async (ruleId: string) => {
    try {
      await api.activateRule(ruleId);
      queryClient.invalidateQueries({ queryKey: ["rules"] });
    } catch (err: unknown) {
      console.error("Failed to activate:", err);
    }
  };

  const handleArchive = async (ruleId: string) => {
    try {
      await api.archiveRule(ruleId);
      queryClient.invalidateQueries({ queryKey: ["rules"] });
    } catch (err: unknown) {
      console.error("Failed to archive:", err);
    }
  };

  const handleDraft = async (ruleId: string) => {
    try {
      await api.draftRule(ruleId);
      queryClient.invalidateQueries({ queryKey: ["rules"] });
    } catch (err: unknown) {
      console.error("Failed to draft:", err);
    }
  };

  const handleDelete = async (ruleId: string) => {
    if (!window.confirm("Permanently delete this rule?")) return;
    try {
      await api.deleteRule(ruleId);
      queryClient.invalidateQueries({ queryKey: ["rules"] });
    } catch (err: unknown) {
      console.error("Failed to delete:", err);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRuleText.trim()) return;
    try {
      await api.createRule({
        text: newRuleText.trim(),
        author: "admin",
        reason: newRuleReason.trim() || undefined,
      });
      setNewRuleText("");
      setNewRuleReason("");
      setShowNewRule(false);
      queryClient.invalidateQueries({ queryKey: ["rules"] });
    } catch (err: unknown) {
      console.error("Failed to create:", err);
    }
  };

  return (
    <div className="bg-elevated rounded-lg border border-border overflow-hidden">
      <div className="px-4 py-3 border-b border-border bg-subtle flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield size={18} className="text-accent" strokeWidth={1.5} />
          <h2 className="font-medium text-[15px]">Rules</h2>
          <span className="text-xs px-2 py-0.5 bg-success-dim text-success rounded-full border border-success/20">
            {activeCount} active
          </span>
          {epoch > 0 && (
            <span className="text-xs text-muted-foreground">epoch {epoch}</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="text-xs bg-input border border-border rounded-md px-2 py-1 text-primary focus:outline-none focus:ring-1 focus:ring-accent/50"
          >
            <option value="">All</option>
            <option value="pending">Pending</option>
            <option value="active">Active</option>
            <option value="draft">Draft</option>
            <option value="archived">Archived</option>
          </select>
          <button
            onClick={() => setShowNewRule(!showNewRule)}
            className="p-1.5 hover:bg-subtle rounded-md text-muted-foreground hover:text-primary transition-colors"
          >
            <Plus size={16} />
          </button>
        </div>
      </div>

      {showNewRule && (
        <div className="p-4 border-b border-border bg-subtle/50">
          <form onSubmit={handleCreate} className="space-y-2">
            <input
              type="text"
              value={newRuleText}
              onChange={(e) => setNewRuleText(e.target.value)}
              placeholder="Rule text (e.g., Always summarize long threads)"
              className="w-full px-3 py-2 bg-input border border-border rounded-md text-sm text-primary placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent/50"
              maxLength={500}
            />
            <textarea
              value={newRuleReason}
              onChange={(e) => setNewRuleReason(e.target.value)}
              placeholder="Reason (optional)"
              className="w-full px-3 py-2 bg-input border border-border rounded-md text-sm text-primary placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent/50"
              rows={2}
              maxLength={1000}
            />
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setShowNewRule(false)}
                className="px-3 py-1.5 text-sm border border-border rounded-md text-muted-foreground hover:text-primary hover:bg-subtle transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-3 py-1.5 text-sm bg-accent text-white rounded-md hover:bg-accent-hover transition-colors"
              >
                Propose Rule
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="divide-y divide-border max-h-[600px] overflow-y-auto">
        {isLoading ? (
          <div className="p-8 flex items-center justify-center text-muted-foreground gap-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading rules...
          </div>
        ) : rules.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground text-sm">
            <ScrollText size={32} className="mx-auto mb-3 opacity-40" />
            <p className="font-medium text-primary mb-1">No rules found</p>
            <p className="text-xs">Click + to propose a rule. Only active rules are injected into agent prompts.</p>
          </div>
        ) : (
          rules.map((rule: any) => (
            <div key={rule.id} className="p-4 hover:bg-subtle/50 transition-colors">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs px-2 py-0.5 rounded capitalize ${statusBadgeColors[rule.status] || "bg-subtle text-muted-foreground border border-border"}`}>
                      {rule.status}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      by {rule.author}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-primary">{rule.text}</p>
                  {rule.reason && (
                    <p className="text-xs text-muted-foreground mt-1">{rule.reason}</p>
                  )}
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  {rule.status === "pending" && (
                    <button
                      onClick={() => handleActivate(rule.id)}
                      className="p-1.5 hover:bg-success-dim rounded-md text-success transition-colors"
                      title="Activate"
                    >
                      <CheckCircle size={16} />
                    </button>
                  )}
                  {rule.status === "active" && (
                    <>
                      <button
                        onClick={() => handleDraft(rule.id)}
                        className="p-1.5 hover:bg-blue-900/30 rounded-md text-blue-400 transition-colors"
                        title="Move to draft"
                      >
                        <RotateCcw size={16} />
                      </button>
                      <button
                        onClick={() => handleArchive(rule.id)}
                        className="p-1.5 hover:bg-subtle rounded-md text-muted-foreground hover:text-primary transition-colors"
                        title="Archive"
                      >
                        <Archive size={16} />
                      </button>
                    </>
                  )}
                  {rule.status === "draft" && (
                    <>
                      <button
                        onClick={() => handleActivate(rule.id)}
                        className="p-1.5 hover:bg-success-dim rounded-md text-success transition-colors"
                        title="Activate"
                      >
                        <CheckCircle size={16} />
                      </button>
                      <button
                        onClick={() => handleArchive(rule.id)}
                        className="p-1.5 hover:bg-subtle rounded-md text-muted-foreground hover:text-primary transition-colors"
                        title="Archive"
                      >
                        <Archive size={16} />
                      </button>
                    </>
                  )}
                  {(rule.status === "archived" || rule.status === "pending") && (
                    <button
                      onClick={() => handleDelete(rule.id)}
                      className="p-1.5 hover:bg-destructive-dim rounded-md text-destructive transition-colors"
                      title="Delete"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
