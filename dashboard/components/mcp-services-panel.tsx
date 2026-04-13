"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { formatRelativeTime, getStatusColor } from "@/lib/utils";
import { RegisterMCPDialog } from "./register-mcp-dialog";
import { Plus, Trash2, Activity } from "lucide-react";

export function MCPServicesPanel() {
  const queryClient = useQueryClient();
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);

  const { data: services, isLoading } = useQuery({
    queryKey: ["mcp-services"],
    queryFn: api.listMCPServices,
    refetchInterval: 5000,
  });

  const handleDelete = async (serviceId: string) => {
    if (!confirm(`Delete service "${serviceId}"?`)) return;
    await api.deleteMCPService(serviceId);
    queryClient.invalidateQueries({ queryKey: ["mcp-services"] });
  };

  const handleHeartbeat = async (serviceId: string) => {
    try {
      await api.sendMCPHeartbeat(serviceId);
      queryClient.invalidateQueries({ queryKey: ["mcp-services"] });
    } catch (err: unknown) {
      alert(`Failed to send heartbeat: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  if (isLoading) return <div className="p-4">Loading MCP services...</div>;

  return (
    <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b bg-slate-50 flex items-center justify-between">
        <h2 className="font-semibold">MCP Services</h2>
        <button
          onClick={() => setIsRegisterOpen(true)}
          className="flex items-center gap-1 px-3 py-1 text-xs bg-slate-900 text-white rounded-md hover:bg-slate-800"
        >
          <Plus size={14} /> Register
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-600">
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
          <tbody className="divide-y">
            {services?.map((service) => (
              <tr key={service.service_id} className="hover:bg-slate-50">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${getStatusColor(service.status)}`} />
                    <span className="capitalize">{service.status}</span>
                  </div>
                </td>
                <td className="px-4 py-3 font-mono text-xs">{service.service_id}</td>
                <td className="px-4 py-3">{service.name}</td>
                <td className="px-4 py-3 text-slate-500 text-xs font-mono">{service.endpoint}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {service.capabilities.map((cap) => (
                      <span key={cap} className="px-2 py-0.5 bg-slate-100 rounded text-xs">{cap}</span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs ${service.protocol === 'mcp' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'}`}>
                    {service.protocol || 'rest'}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-500">
                  {service.last_heartbeat ? formatRelativeTime(service.last_heartbeat) : "Never"}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleHeartbeat(service.service_id)}
                      className="text-slate-400 hover:text-blue-500"
                      title="Send heartbeat"
                    >
                      <Activity size={14} />
                    </button>
                    <button
                      onClick={() => handleDelete(service.service_id)}
                      className="text-slate-400 hover:text-red-500"
                      title="Delete service"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {services?.length === 0 && (
          <div className="p-8 text-center text-slate-500">No MCP services registered</div>
        )}
      </div>
      <RegisterMCPDialog isOpen={isRegisterOpen} onClose={() => setIsRegisterOpen(false)} />
    </div>
  );
}
