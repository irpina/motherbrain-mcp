"use client";

import { api } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import {
  formatRelativeTime,
  truncateId,
  getStatusColor,
} from "@/lib/utils";

export function AgentsPanel() {
  const { data: agents, isLoading } = useQuery({
    queryKey: ["agents"],
    queryFn: api.listAgents,
    refetchInterval: 5000,
  });

  if (isLoading) {
    return <div className="p-4">Loading agents...</div>;
  }

  const now = new Date();

  return (
    <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b bg-slate-50">
        <h2 className="font-semibold">Agents</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-2 text-left font-medium">Status</th>
              <th className="px-4 py-2 text-left font-medium">Agent ID</th>
              <th className="px-4 py-2 text-left font-medium">Platform</th>
              <th className="px-4 py-2 text-left font-medium">Capabilities</th>
              <th className="px-4 py-2 text-left font-medium">Last Heartbeat</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {agents?.map((agent) => {
              const heartbeatAge =
                (now.getTime() - new Date(agent.last_heartbeat).getTime()) /
                1000;
              const isStale = heartbeatAge > 30;
              const statusColor = isStale
                ? "bg-red-500"
                : getStatusColor(agent.status);

              return (
                <tr key={agent.agent_id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-2 h-2 rounded-full ${statusColor}`}
                      />
                      <span className="capitalize">{agent.status}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-mono">
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
                    {formatRelativeTime(agent.last_heartbeat)}
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
