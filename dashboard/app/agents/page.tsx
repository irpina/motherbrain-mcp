"use client";

import { AgentsPanel } from "@/components/agents-panel";

export default function AgentsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Agents</h1>
        <p className="text-slate-500">Manage your agent fleet</p>
      </div>
      <AgentsPanel />
    </div>
  );
}
