"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useQueryClient } from "@tanstack/react-query";

interface RegisterMCPDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

export function RegisterMCPDialog({ isOpen, onClose }: RegisterMCPDialogProps) {
  const queryClient = useQueryClient();
  const [serviceId, setServiceId] = useState("");
  const [name, setName] = useState("");
  const [endpoint, setEndpoint] = useState("");
  const [capabilities, setCapabilities] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [protocol, setProtocol] = useState("rest");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const resetForm = () => {
    setServiceId("");
    setName("");
    setEndpoint("");
    setCapabilities("");
    setApiKey("");
    setProtocol("rest");
    setError(null);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const capsArray = capabilities
        .split(",")
        .map((c) => c.trim())
        .filter((c) => c.length > 0);

      await api.registerMCPService({
        service_id: serviceId.trim(),
        name: name.trim(),
        endpoint: endpoint.trim(),
        capabilities: capsArray,
        api_key: apiKey.trim() || undefined,
        protocol: protocol,
      });

      queryClient.invalidateQueries({ queryKey: ["mcp-services"] });
      handleClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to register service");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-elevated rounded-lg shadow-lg w-full max-w-md">
        <div className="px-4 py-3 border-b">
          <h2 className="text-lg font-medium">Register MCP Service</h2>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {error && (
            <div className="p-3 bg-destructive-dim border border-destructive/20 rounded text-destructive text-sm">
              {error}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium mb-1">Service ID</label>
            <input
              type="text"
              value={serviceId}
              onChange={(e) => setServiceId(e.target.value)}
              placeholder="e.g., code-gen-mcp"
              className="w-full px-3 py-2 bg-input border border-border rounded-md text-sm text-primary placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent/50"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Code Generation Service"
              className="w-full px-3 py-2 bg-input border border-border rounded-md text-sm text-primary placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent/50"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Endpoint</label>
            <input
              type="text"
              value={endpoint}
              onChange={(e) => setEndpoint(e.target.value)}
              placeholder="http://localhost:8001"
              className="w-full px-3 py-2 bg-input border border-border rounded-md text-sm font-mono text-primary placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent/50"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              Capabilities <span className="text-muted-foreground font-normal">(comma-separated)</span>
            </label>
            <input
              type="text"
              value={capabilities}
              onChange={(e) => setCapabilities(e.target.value)}
              placeholder="e.g., generate_code, python"
              className="w-full px-3 py-2 bg-input border border-border rounded-md text-sm text-primary placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent/50"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Protocol</label>
            <select
              value={protocol}
              onChange={(e) => setProtocol(e.target.value)}
              className="w-full px-3 py-2 bg-input border border-border rounded-md text-sm text-primary placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent/50"
            >
              <option value="rest">REST (POST /execute)</option>
              <option value="mcp">MCP (JSON-RPC /mcp)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">
              API Key <span className="text-muted-foreground font-normal">(optional)</span>
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Leave blank if not required"
              className="w-full px-3 py-2 bg-input border border-border rounded-md text-sm text-primary placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent/50"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 text-sm border rounded-md hover:bg-subtle"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-sm bg-accent text-white rounded-md hover:bg-accent-hover disabled:opacity-50"
            >
              {isSubmitting ? "Registering..." : "Register"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
