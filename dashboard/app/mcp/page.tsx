"use client";

import { MCPServicesPanel } from "@/components/mcp-services-panel";

export default function MCPPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-medium">MCP Services</h1>
        <p className="text-muted-foreground">Register and monitor MCP service endpoints</p>
      </div>
      <MCPServicesPanel />
    </div>
  );
}
