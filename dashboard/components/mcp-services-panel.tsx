"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { formatRelativeTime, getProtocolBadgeColor } from "@/lib/utils";
import { RegisterMCPDialog } from "./register-mcp-dialog";
import { Plus, Trash2, Activity, Loader2 } from "lucide-react";

export function MCPServicesPanel() {
  const queryClient = useQueryClient();
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [heartbeatingId, setHeartbeatingId] = useState<string | null>(null);

  const { data: services, isLoading } = useQuery({
    queryKey: ["mcp-services"],
    queryFn: api.listMCPServices,
    refetchInterval: 5000,
  });

  const handleDelete = async (serviceId: string) => {
    if (!confirm(`Delete service "${serviceId}"?`)) return;
    setDeletingId(serviceId);
    try {
      await api.deleteMCPService(serviceId);
      queryClient.invalidateQueries({ queryKey: ["mcp-services"] });
    } finally {
      setDeletingId(null);
    }
  };

  const handleHeartbeat = async (serviceId: string) => {
    setHeartbeatingId(serviceId);
    try {
      await api.sendMCPHeartbeat(serviceId);
      queryClient.invalidateQueries({ queryKey: ["mcp-services"] });
    } catch (err: unknown) {
      console.error("Failed to send heartbeat:", err);
    } finally {
      setHeartbeatingId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-elevated rounded-lg border border-border overflow-hidden">
        <div className="px-4 py-3 border-b border-border bg-subtle">
          <h2 className="font-medium text-[15px]">MCP Services</h2>
        </div>
        <div className="p-8 flex items-center justify-center text-muted-foreground gap-2">
          <Loader2 className="w-4 h-4 animate-spin" />
          Loading MCP services...
        </div>
      </div>
    );
  }

  return (
    <div className="bg-elevated rounded-lg border border-border overflow-hidden">
      <div className="px-4 py-3 border-b border-border bg-subtle flex items-center justify-between">
        <h2 className="font-medium text-[15px]">MCP Services</h2>
        <button
          onClick={() => setIsRegisterOpen(true)}
          className="flex items-center gap-1 px-3 py-1.5 text-xs bg-accent text-white rounded-md hover:bg-accent-hover transition-colors"
        >
          <Plus size={14} /> Register
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-elevated text-muted-foreground border-b border-border">
            <tr>
              <th className="px-4 py-2 text-left font-medium">Status</th>
              <th className="px-4 py-2 text-left font-medium">Service ID</th>
              <th className="px-4 py-2 text-left font-medium">Name</th>
              <th className="px-4 py-2 text-left font-medium">Endpoint</th>
              <th className="px-4 py-2 text-left font-medium">Capabilities</th>
              <th className="px-4 py-2 text-left font-medium">Protocol</th>
              <th className="px-4 py-2 text-left font-medium">Last Heartbeat</th>
              <th className="px-4 py-2 text-left font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {services?.map((service) => (
              <tr key={service.service_id} className="hover:bg-subtle/50 transition-colors">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`w-2.5 h-2.5 rounded-full ${
                        service.status === "online"
                          ? "bg-success shadow-[0_0_6px_var(--success)]"
                          : service.status === "offline"
                          ? "bg-danger"
                          : "bg-muted-foreground/40"
                      }`}
                    />
                    <span className="capitalize text-sm">{service.status}</span>
                  </div>
                </td>
                <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{service.service_id}</td>
                <td className="px-4 py-3 text-primary">{service.name}</td>
                <td className="px-4 py-3 text-muted-foreground text-xs font-mono">{service.endpoint}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {service.capabilities.map((cap: string) => (
                      <span key={cap} className="px-2 py-0.5 bg-subtle border border-border rounded text-xs text-muted-foreground">
                        {cap}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs ${getProtocolBadgeColor(service.protocol)}`}>
                    {service.protocol || "rest"}
                  </span>
                </td>
                <td className="px-4 py-3 text-muted-foreground text-xs">
                  {service.last_heartbeat ? formatRelativeTime(service.last_heartbeat) : "Never"}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleHeartbeat(service.service_id)}
                      disabled={heartbeatingId === service.service_id}
                      className="text-muted-foreground hover:text-accent transition-colors disabled:opacity-50"
                      title="Send heartbeat"
                    >
                      {heartbeatingId === service.service_id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Activity size={14} />
                      )}
                    </button>
                    <button
                      onClick={() => handleDelete(service.service_id)}
                      disabled={deletingId === service.service_id}
                      className="text-muted-foreground hover:text-destructive transition-colors disabled:opacity-50"
                      title="Delete service"
                    >
                      {deletingId === service.service_id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Trash2 size={14} />
                      )}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {services?.length === 0 && (
          <div className="p-8 text-center text-muted-foreground text-sm">
            <p className="font-medium text-primary mb-1">No MCP services registered</p>
            <p className="text-xs">Click Register to add a service endpoint, or use the /mcp/register API.</p>
          </div>
        )}
      </div>
      <RegisterMCPDialog isOpen={isRegisterOpen} onClose={() => setIsRegisterOpen(false)} />
    </div>
  );
}
