"use client";

import { RulesPanel } from "@/components/rules-panel";

export default function RulesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-medium">Rules</h1>
        <p className="text-muted-foreground">
          Shared working style for the agent collective. Agents propose; humans activate.
        </p>
      </div>
      <RulesPanel />
    </div>
  );
}
