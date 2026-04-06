"use client";

import { MCPServicesPanel } from "@/components/mcp-services-panel";

export default function MCPPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">MCP Services</h1>
        <p className="text-slate-500">Register and monitor MCP service endpoints</p>
      </div>
      <MCPServicesPanel />
    </div>
  );
}
