"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ScrollText, CheckCircle, Archive, RotateCcw, Trash2, Plus, Shield } from "lucide-react";

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  active: "bg-green-100 text-green-800",
  archived: "bg-slate-100 text-slate-500",
  draft: "bg-blue-100 text-blue-800",
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
      alert(`Failed to activate: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const handleArchive = async (ruleId: string) => {
    try {
      await api.archiveRule(ruleId);
      queryClient.invalidateQueries({ queryKey: ["rules"] });
    } catch (err: unknown) {
      alert(`Failed to archive: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const handleDraft = async (ruleId: string) => {
    try {
      await api.draftRule(ruleId);
      queryClient.invalidateQueries({ queryKey: ["rules"] });
    } catch (err: unknown) {
      alert(`Failed to draft: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const handleDelete = async (ruleId: string) => {
    if (!window.confirm("Permanently delete this rule?")) return;
    try {
      await api.deleteRule(ruleId);
      queryClient.invalidateQueries({ queryKey: ["rules"] });
    } catch (err: unknown) {
      alert(`Failed to delete: ${err instanceof Error ? err.message : String(err)}`);
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
      alert(`Failed to create: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  return (
    <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b bg-slate-50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield size={18} className="text-blue-600" />
          <h2 className="font-semibold">Rules</h2>
          <span className="text-xs px-2 py-0.5 bg-green-100 text-green-800 rounded-full">
            {activeCount} active
          </span>
          {epoch > 0 && (
            <span className="text-xs text-slate-400">epoch {epoch}</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="text-xs border rounded px-2 py-1"
          >
            <option value="">All</option>
            <option value="pending">Pending</option>
            <option value="active">Active</option>
            <option value="draft">Draft</option>
            <option value="archived">Archived</option>
          </select>
          <button
            onClick={() => setShowNewRule(!showNewRule)}
            className="p-1 hover:bg-slate-200 rounded"
          >
            <Plus size={16} />
          </button>
        </div>
      </div>

      {showNewRule && (
        <div className="p-4 border-b bg-slate-50">
          <form onSubmit={handleCreate} className="space-y-2">
            <input
              type="text"
              value={newRuleText}
              onChange={(e) => setNewRuleText(e.target.value)}
              placeholder="Rule text (e.g., Always summarize long threads)"
              className="w-full px-3 py-2 border rounded text-sm"
              maxLength={500}
            />
            <textarea
              value={newRuleReason}
              onChange={(e) => setNewRuleReason(e.target.value)}
              placeholder="Reason (optional)"
              className="w-full px-3 py-2 border rounded text-sm"
              rows={2}
              maxLength={1000}
            />
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setShowNewRule(false)}
                className="px-3 py-1 text-sm border rounded hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Propose Rule
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="divide-y max-h-[600px] overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-sm text-slate-400">Loading rules...</div>
        ) : rules.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            <ScrollText size={32} className="mx-auto mb-2 opacity-50" />
            No rules found
          </div>
        ) : (
          rules.map((rule: any) => (
            <div key={rule.id} className="p-4 hover:bg-slate-50">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs px-2 py-0.5 rounded capitalize ${statusColors[rule.status] || "bg-slate-100"}`}>
                      {rule.status}
                    </span>
                    <span className="text-xs text-slate-400">
                      by {rule.author}
                    </span>
                  </div>
                  <p className="text-sm font-medium">{rule.text}</p>
                  {rule.reason && (
                    <p className="text-xs text-slate-500 mt-1">{rule.reason}</p>
                  )}
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  {rule.status === "pending" && (
                    <button
                      onClick={() => handleActivate(rule.id)}
                      className="p-1.5 hover:bg-green-100 rounded text-green-600"
                      title="Activate"
                    >
                      <CheckCircle size={16} />
                    </button>
                  )}
                  {rule.status === "active" && (
                    <>
                      <button
                        onClick={() => handleDraft(rule.id)}
                        className="p-1.5 hover:bg-blue-100 rounded text-blue-600"
                        title="Move to draft"
                      >
                        <RotateCcw size={16} />
                      </button>
                      <button
                        onClick={() => handleArchive(rule.id)}
                        className="p-1.5 hover:bg-slate-200 rounded text-slate-500"
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
                        className="p-1.5 hover:bg-green-100 rounded text-green-600"
                        title="Activate"
                      >
                        <CheckCircle size={16} />
                      </button>
                      <button
                        onClick={() => handleArchive(rule.id)}
                        className="p-1.5 hover:bg-slate-200 rounded text-slate-500"
                        title="Archive"
                      >
                        <Archive size={16} />
                      </button>
                    </>
                  )}
                  {(rule.status === "archived" || rule.status === "pending") && (
                    <button
                      onClick={() => handleDelete(rule.id)}
                      className="p-1.5 hover:bg-red-100 rounded text-red-500"
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
