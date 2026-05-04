"use client";

import { RulesPanel } from "@/components/rules-panel";

export default function RulesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Rules</h1>
        <p className="text-slate-500">
          Shared working style for the agent collective. Agents propose; humans activate.
        </p>
      </div>
      <RulesPanel />
    </div>
  );
}
