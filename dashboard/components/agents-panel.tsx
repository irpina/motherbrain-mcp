"use client";

import { api } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  formatRelativeTime,
  truncateId,
} from "@/lib/utils";

const presenceColors: Record<string, string> = {
  active: "bg-green-100 text-green-800",
  idle: "bg-yellow-100 text-yellow-800",
  away: "bg-slate-100 text-slate-600",
  registered: "bg-blue-50 text-blue-600",
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
      alert(`Failed to remove agent: ${err}`);
    }
  };

  if (isLoading) {
    return <div className="p-4">Loading agents...</div>;
  }

  return (
    <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b bg-slate-50">
        <h2 className="font-semibold">Agents</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-600">
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
          <tbody className="divide-y">
            {agents?.map((agent) => {
              const displayName = agent.name
                ? agent.hostname
                  ? `${agent.name} @ ${agent.hostname}`
                  : agent.name
                : truncateId(agent.agent_id);
              const presence = agent.presence || "registered";

              return (
                <tr key={agent.agent_id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs ${presenceColors[presence] ?? "bg-slate-100 text-slate-600"}`}>
                      {presenceLabels[presence] ?? presence}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-medium">
                    {displayName}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-500">
                    {truncateId(agent.agent_id)}
                  </td>
                  <td className="px-4 py-3">{agent.platform}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(agent.capabilities)
                        .filter(([_, v]) => v)
                        .map(([key]) => (
                          <span
                            key={key}
                            className="px-2 py-0.5 bg-slate-100 rounded text-xs"
                          >
                            {key}
                          </span>
                        ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {agent.last_heartbeat ? formatRelativeTime(agent.last_heartbeat) : "Never"}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleRemove(agent.agent_id, displayName)}
                      className="px-2 py-1 text-xs bg-red-50 text-red-600 rounded hover:bg-red-100 transition-colors"
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
          <div className="p-8 text-center text-slate-500">No agents registered</div>
        )}
      </div>
    </div>
  );
}
