"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { formatRelativeTime } from "@/lib/utils";
import { Bot, Trash2, Terminal } from "lucide-react";
import { AgentTerminalModal } from "./agent-terminal-modal";

export function SpawnedAgentsPanel() {
  const queryClient = useQueryClient();
  const { data: spawned, isLoading } = useQuery({
    queryKey: ["agents", "spawned"],
    queryFn: api.listSpawnedAgents,
    refetchInterval: 5000,
  });

  const [terminalAgent, setTerminalAgent] = useState<{
    id: string;
    type: string;
    containerId: string;
  } | null>(null);

  const handleKill = async (id: string, agentType: string) => {
    if (!window.confirm(`Kill ${agentType} agent?`)) return;
    try {
      const res = await api.killSpawnedAgent(id);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      queryClient.invalidateQueries({ queryKey: ["agents", "spawned"] });
      queryClient.invalidateQueries({ queryKey: ["agents", "spawnable"] });
    } catch (err: unknown) {
      alert(`Failed to kill agent: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  if (isLoading) {
    return <div className="p-4">Loading spawned agents...</div>;
  }

  const running = spawned?.filter((a: any) => a.status === "running") || [];

  return (
    <>
      <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        <div className="px-4 py-3 border-b bg-slate-50 flex items-center justify-between">
          <h2 className="font-semibold flex items-center gap-2">
            <Bot size={18} />
            Spawned Agents
          </h2>
          <span className="text-xs text-slate-500">
            {running.length} running
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-2 text-left font-medium">Type</th>
                <th className="px-4 py-2 text-left font-medium">Channel</th>
                <th className="px-4 py-2 text-left font-medium">Task</th>
                <th className="px-4 py-2 text-left font-medium">Status</th>
                <th className="px-4 py-2 text-left font-medium">Started</th>
                <th className="px-4 py-2 text-left font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {spawned?.map((agent: any) => (
                <tr key={agent.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <span className="capitalize font-medium">{agent.agent_type}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-slate-600">#{agent.channel}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-slate-500 truncate max-w-[200px] block">
                      {agent.task || "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`px-2 py-0.5 rounded text-xs ${
                        agent.status === "running"
                          ? "bg-green-100 text-green-800"
                          : agent.status === "stopped"
                          ? "bg-slate-100 text-slate-600"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {agent.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {formatRelativeTime(agent.created_at)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      {agent.status === "running" && (
                        <>
                          <button
                            onClick={() =>
                              setTerminalAgent({
                                id: agent.id,
                                type: agent.agent_type,
                                containerId: agent.container_id,
                              })
                            }
                            className="p-1 text-blue-500 hover:bg-blue-50 rounded"
                            title="Open terminal"
                          >
                            <Terminal size={16} />
                          </button>
                          <button
                            onClick={() => handleKill(agent.id, agent.agent_type)}
                            className="p-1 text-red-500 hover:bg-red-50 rounded"
                            title="Kill agent"
                          >
                            <Trash2 size={16} />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {spawned?.length === 0 && (
            <div className="p-8 text-center text-slate-500">
              No spawned agents yet
            </div>
          )}
        </div>
      </div>

      <AgentTerminalModal
        isOpen={!!terminalAgent}
        onClose={() => setTerminalAgent(null)}
        agentId={terminalAgent?.id || ""}
        agentType={terminalAgent?.type || ""}
        containerId={terminalAgent?.containerId || ""}
      />
    </>
  );
}
