"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useQueryClient, useQuery } from "@tanstack/react-query";

interface CreateJobDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CreateJobDialog({ isOpen, onClose }: CreateJobDialogProps) {
  const queryClient = useQueryClient();
  const [type, setType] = useState("");
  const [payload, setPayload] = useState("{}");
  const [requirements, setRequirements] = useState("");
  const [priority, setPriority] = useState("medium");
  const [assignedAgent, setAssignedAgent] = useState("");
  const [contextJobIds, setContextJobIds] = useState("");
  const [skillKey, setSkillKey] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const { data: agents } = useQuery({
    queryKey: ["agents"],
    queryFn: api.listAgents,
  });

  const onlineAgents = agents?.filter(a => a.status === "online") ?? [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError("");

    try {
      const parsedPayload = JSON.parse(payload);
      const reqArray = requirements
        .split(",")
        .map((r) => r.trim())
        .filter(Boolean);
      
      // Parse context job IDs (comma-separated UUIDs)
      const contextIdsArray = contextJobIds
        .split(",")
        .map((id) => id.trim())
        .filter(Boolean);

      await api.createJob({
        type,
        payload: parsedPayload,
        requirements: reqArray,
        priority,
        created_by: "dashboard",
        assigned_agent: assignedAgent || null,
        context_job_ids: contextIdsArray,
        skill_key: skillKey || null,
      });

      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      onClose();
      setType("");
      setPayload("{}");
      setRequirements("");
      setPriority("medium");
      setAssignedAgent("");
      setContextJobIds("");
      setSkillKey("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create job");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-md p-6">
        <h2 className="text-lg font-semibold mb-4">Create New Job</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Job Type</label>
            <input
              type="text"
              value={type}
              onChange={(e) => setType(e.target.value)}
              placeholder="e.g., code_review, implement_feature"
              className="w-full px-3 py-2 border rounded-md text-sm"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Payload (JSON)
            </label>
            <textarea
              value={payload}
              onChange={(e) => setPayload(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border rounded-md text-sm font-mono"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Requirements (comma-separated)
            </label>
            <input
              type="text"
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              placeholder="e.g., python, code_generation"
              className="w-full px-3 py-2 border rounded-md text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Priority</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="w-full px-3 py-2 border rounded-md text-sm"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Assign to Agent <span className="text-slate-400 font-normal">(optional)</span>
            </label>
            <select
              value={assignedAgent}
              onChange={(e) => setAssignedAgent(e.target.value)}
              className="w-full px-3 py-2 border rounded-md text-sm bg-white"
            >
              <option value="">Any available agent (general queue)</option>
              {onlineAgents.map(a => (
                <option key={a.agent_id} value={a.agent_id}>
                  {a.platform} — {a.agent_id.slice(0, 8)}... ({a.status})
                </option>
              ))}
            </select>
            {onlineAgents.length === 0 && (
              <p className="text-xs text-slate-400 mt-1">No online agents</p>
            )}
          </div>

          <div className="border-t pt-4 mt-4">
            <h3 className="text-sm font-medium text-slate-700 mb-3">Context References (Optional)</h3>
            
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium mb-1">
                  Context Job IDs
                  <span className="text-slate-400 font-normal ml-1">— Comma-separated prior job UUIDs</span>
                </label>
                <input
                  type="text"
                  value={contextJobIds}
                  onChange={(e) => setContextJobIds(e.target.value)}
                  placeholder="e.g., uuid-1, uuid-2"
                  className="w-full px-3 py-2 border rounded-md text-sm"
                />
                <p className="text-xs text-slate-400 mt-1">
                  Agent will receive results/payloads from these jobs as context
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">
                  Skill Key
                  <span className="text-slate-400 font-normal ml-1">— From context/skills store</span>
                </label>
                <input
                  type="text"
                  value={skillKey}
                  onChange={(e) => setSkillKey(e.target.value)}
                  placeholder="e.g., skills.code_review"
                  className="w-full px-3 py-2 border rounded-md text-sm"
                />
                <p className="text-xs text-slate-400 mt-1">
                  Skill value will be inlined when agent picks up the job
                </p>
              </div>
            </div>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border rounded-md text-sm hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 px-4 py-2 bg-slate-900 text-white rounded-md text-sm hover:bg-slate-800 disabled:opacity-50"
            >
              {isSubmitting ? "Creating..." : "Create Job"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
