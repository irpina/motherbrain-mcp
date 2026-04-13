"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, AlertCircle, Loader2 } from "lucide-react";

interface SpawnAgentDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SpawnAgentDialog({ isOpen, onClose }: SpawnAgentDialogProps) {
  const queryClient = useQueryClient();
  const [selectedType, setSelectedType] = useState("");
  const [channel, setChannel] = useState("general");
  const [task, setTask] = useState("");
  const [isSpawning, setIsSpawning] = useState(false);

  const { data: spawnable } = useQuery({
    queryKey: ["agents", "spawnable"],
    queryFn: api.listSpawnableAgents,
    enabled: isOpen,
  });

  const handleSpawn = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedType || !channel) return;

    setIsSpawning(true);
    try {
      await api.spawnAgent(selectedType, channel, task || undefined);
      queryClient.invalidateQueries({ queryKey: ["agents", "spawned"] });
      queryClient.invalidateQueries({ queryKey: ["agents", "spawnable"] });
      onClose();
      setSelectedType("");
      setChannel("general");
      setTask("");
    } catch (err: unknown) {
      alert(`Failed to spawn agent: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsSpawning(false);
    }
  };

  if (!isOpen) return null;

  const selectedAgent = spawnable?.find((a: any) => a.type === selectedType);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-[28rem] max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Bot size={20} />
            Spawn Agent
          </h2>

          <form onSubmit={handleSpawn} className="space-y-4">
            {/* Agent Type */}
            <div>
              <label className="block text-sm font-medium mb-1">Agent Type</label>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="w-full px-3 py-2 border rounded-md"
                required
              >
                <option value="">Select an agent...</option>
                {spawnable?.map((agent: any) => (
                  <option key={agent.type} value={agent.type}>
                    {agent.name} {agent.has_credentials ? "✓" : "(no credentials)"}
                  </option>
                ))}
              </select>
              {selectedAgent && !selectedAgent.has_credentials && (
                <div className="mt-2 p-2 bg-yellow-50 text-yellow-800 text-sm rounded flex items-start gap-2">
                  <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
                  <span>
                    No API credentials stored for this agent type. Add them in{" "}
                    <a href="/admin/settings" className="underline">
                      Settings
                    </a>{" "}
                    first.
                  </span>
                </div>
              )}
            </div>

            {/* Channel */}
            <div>
              <label className="block text-sm font-medium mb-1">Channel</label>
              <input
                type="text"
                value={channel}
                onChange={(e) => setChannel(e.target.value)}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="general"
                required
              />
              <p className="text-xs text-slate-500 mt-1">
                The channel the agent will join and monitor
              </p>
            </div>

            {/* Task */}
            <div>
              <label className="block text-sm font-medium mb-1">
                Initial Task (optional)
              </label>
              <textarea
                value={task}
                onChange={(e) => setTask(e.target.value)}
                className="w-full px-3 py-2 border rounded-md h-24 resize-none"
                placeholder="E.g., Review the codebase for security issues..."
              />
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2 border rounded-md hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={
                  !selectedType ||
                  !channel ||
                  isSpawning ||
                  (selectedAgent && !selectedAgent.has_credentials)
                }
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isSpawning && <Loader2 size={16} className="animate-spin" />}
                {isSpawning ? "Spawning..." : "Spawn Agent"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
