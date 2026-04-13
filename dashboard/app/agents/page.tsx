"use client";

import { useState } from "react";
import { AgentsPanel } from "@/components/agents-panel";
import { SpawnedAgentsPanel } from "@/components/spawned-agents-panel";
import { SpawnAgentDialog } from "@/components/spawn-agent-dialog";
import { Plus } from "lucide-react";

export default function AgentsPage() {
  const [showSpawnDialog, setShowSpawnDialog] = useState(false);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Agents</h1>
          <p className="text-slate-500">Manage your agent fleet</p>
        </div>
        <button
          onClick={() => setShowSpawnDialog(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus size={18} />
          Spawn Agent
        </button>
      </div>

      <SpawnedAgentsPanel />
      <AgentsPanel />

      <SpawnAgentDialog
        isOpen={showSpawnDialog}
        onClose={() => setShowSpawnDialog(false)}
      />
    </div>
  );
}
