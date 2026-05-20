"use client";

import { api } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { formatRelativeTime, truncateId } from "@/lib/utils";
import { Loader2 } from "lucide-react";

const presenceBadgeColors: Record<string, string> = {
  active: "bg-success-dim text-success border border-success/20",
  idle: "bg-warning-dim text-warning border border-warning/20",
  away: "bg-subtle text-muted-foreground border border-border",
  registered: "bg-blue-900/40 text-blue-300 border border-blue-800/50",
};

const presenceLabels: Record<string, string> = {
  active: "Active",
  idle: "Idle",
  away: "Away",
  registered: "Registered",
};

export function AgentsPanel() {
  const queryClient = useQueryClient();
  const { data: agents, isLoading } = useQuery({
    queryKey: ["agents"],
    queryFn: api.listAgents,
    refetchInterval: 5000,
  });

  const handleRemove = async (agentId: string, displayName: string) => {
    if (!window.confirm(`Remove agent "${displayName}"?`)) return;
    try {
      const res = await api.deleteAgent(agentId);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      queryClient.invalidateQueries({ queryKey: ["agents"] });
    } catch (err) {
      console.error("Failed to remove agent:", err);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-elevated rounded-lg border border-border overflow-hidden">
        <div className="px-4 py-3 border-b border-border bg-subtle">
          <h2 className="font-medium text-[15px]">Agents</h2>
        </div>
        <div className="p-8 flex items-center justify-center text-muted-foreground gap-2">
          <Loader2 className="w-4 h-4 animate-spin" />
          Loading agents...
        </div>
      </div>
    );
  }

  return (
    <div className="bg-elevated rounded-lg border border-border overflow-hidden">
      <div className="px-4 py-3 border-b border-border bg-subtle">
        <h2 className="font-medium text-[15px]">Agents</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-elevated text-muted-foreground border-b border-border">
            <tr>
              <th className="px-4 py-2 text-left font-medium">Presence</th>
              <th className="px-4 py-2 text-left font-medium">Name</th>
              <th className="px-4 py-2 text-left font-medium">Agent ID</th>
              <th className="px-4 py-2 text-left font-medium">Platform</th>
              <th className="px-4 py-2 text-left font-medium">Capabilities</th>
              <th className="px-4 py-2 text-left font-medium">Last Heartbeat</th>
              <th className="px-4 py-2 text-left font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {agents?.map((agent) => {
              const displayName = agent.name
                ? agent.hostname
                  ? `${agent.name} @ ${agent.hostname}`
                  : agent.name
                : truncateId(agent.agent_id);
              const presence = agent.presence || "registered";

              return (
                <tr key={agent.agent_id} className="hover:bg-subtle/50 transition-colors">
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs ${presenceBadgeColors[presence] ?? "bg-subtle text-muted-foreground border border-border"}`}>
                      {presenceLabels[presence] ?? presence}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-medium text-primary">
                    {displayName}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                    {truncateId(agent.agent_id)}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{agent.platform}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(agent.capabilities)
                        .filter(([_, v]) => v)
                        .map(([key]) => (
                          <span
                            key={key}
                            className="px-2 py-0.5 bg-subtle border border-border rounded text-xs text-muted-foreground"
                          >
                            {key}
                          </span>
                        ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground text-xs">
                    {agent.last_heartbeat ? formatRelativeTime(agent.last_heartbeat) : "Never"}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleRemove(agent.agent_id, displayName)}
                      className="px-2 py-1 text-xs bg-destructive-dim text-destructive border border-destructive/20 rounded hover:bg-destructive/20 transition-colors"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {agents?.length === 0 && (
          <div className="p-8 text-center text-muted-foreground text-sm">
            <p className="font-medium text-primary mb-1">No agents registered</p>
            <p className="text-xs">Agents self-register via the /agents/register API endpoint.</p>
          </div>
        )}
      </div>
    </div>
  );
}
