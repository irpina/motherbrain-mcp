"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";

interface Group {
  group_id: string;
  name: string;
  description?: string;
  allowed_service_ids: string[];
  created_at: string;
}

interface MCPService {
  service_id: string;
  name: string;
  endpoint: string;
  capabilities: string[];
  status: string;
}

export default function GroupsAdminPage() {
  const queryClient = useQueryClient();
  const [showNewGroupForm, setShowNewGroupForm] = useState(false);
  const [newGroupName, setNewGroupName] = useState("");
  const [newGroupDescription, setNewGroupDescription] = useState("");
  const [editingGroup, setEditingGroup] = useState<Group | null>(null);
  const [selectedServices, setSelectedServices] = useState<string[]>([]);

  const { data: groups, isLoading } = useQuery({
    queryKey: ["admin", "groups"],
    queryFn: api.listGroups,
    refetchInterval: 5000,
  });

  const { data: services } = useQuery({
    queryKey: ["mcp-services"],
    queryFn: api.listMCPServices,
  });

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createGroup({
        name: newGroupName,
        description: newGroupDescription || undefined,
        allowed_service_ids: [],
      });
      setNewGroupName("");
      setNewGroupDescription("");
      setShowNewGroupForm(false);
      queryClient.invalidateQueries({ queryKey: ["admin", "groups"] });
    } catch (err: unknown) {
      alert(`Failed to create group: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const handleDeleteGroup = async (groupId: string, name: string) => {
    if (!window.confirm(`Delete group "${name}"?`)) return;
    try {
      const res = await api.deleteGroup(groupId);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      queryClient.invalidateQueries({ queryKey: ["admin", "groups"] });
    } catch (err: unknown) {
      alert(`Failed to delete group: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const startEditing = (group: Group) => {
    setEditingGroup(group);
    setSelectedServices(group.allowed_service_ids || []);
  };

  const handleSavePermissions = async () => {
    if (!editingGroup) return;
    try {
      await api.updateGroup(editingGroup.group_id, {
        allowed_service_ids: selectedServices,
      });
      setEditingGroup(null);
      queryClient.invalidateQueries({ queryKey: ["admin", "groups"] });
    } catch (err: unknown) {
      alert(`Failed to update permissions: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const toggleService = (serviceId: string) => {
    setSelectedServices((prev) =>
      prev.includes(serviceId)
        ? prev.filter((id) => id !== serviceId)
        : [...prev, serviceId]
    );
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Groups</h1>
        <button
          onClick={() => setShowNewGroupForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          New Group
        </button>
      </div>

      {showNewGroupForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg w-96">
            <h2 className="text-lg font-semibold mb-4">Create New Group</h2>
            <form onSubmit={handleCreateGroup} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <input
                  type="text"
                  value={newGroupName}
                  onChange={(e) => setNewGroupName(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description (optional)</label>
                <input
                  type="text"
                  value={newGroupDescription}
                  onChange={(e) => setNewGroupDescription(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewGroupForm(false)}
                  className="flex-1 px-4 py-2 border rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {editingGroup && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg shadow-lg w-[32rem] max-h-[80vh] overflow-y-auto">
            <h2 className="text-lg font-semibold mb-2">
              Edit Permissions: {editingGroup.name}
            </h2>
            <p className="text-sm text-slate-500 mb-4">
              Select which MCP services members of this group can access.
            </p>
            <div className="space-y-2 mb-4">
              {services?.map((service) => (
                <label
                  key={service.service_id}
                  className="flex items-center gap-3 p-2 border rounded-md cursor-pointer hover:bg-slate-50"
                >
                  <input
                    type="checkbox"
                    checked={selectedServices.includes(service.service_id)}
                    onChange={() => toggleService(service.service_id)}
                    className="w-4 h-4"
                  />
                  <div className="flex-1">
                    <div className="font-medium text-sm">{service.name}</div>
                    <div className="text-xs text-slate-500">{service.service_id}</div>
                  </div>
                  <span
                    className={`text-xs px-2 py-0.5 rounded ${
                      service.status === "online"
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {service.status}
                  </span>
                </label>
              ))}
              {!services?.length && (
                <div className="text-center text-slate-500 py-4">No MCP services registered</div>
              )}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setEditingGroup(null)}
                className="flex-1 px-4 py-2 border rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSavePermissions}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Save Permissions
              </button>
            </div>
          </div>
        </div>
      )}

      {isLoading ? (
        <div>Loading groups...</div>
      ) : (
        <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3 text-left font-medium">Name</th>
                <th className="px-4 py-3 text-left font-medium">Description</th>
                <th className="px-4 py-3 text-left font-medium">Allowed Services</th>
                <th className="px-4 py-3 text-left font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {groups?.map((group) => (
                <tr key={group.group_id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium">{group.name}</td>
                  <td className="px-4 py-3 text-slate-500">{group.description || "—"}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {group.allowed_service_ids?.length ? (
                        group.allowed_service_ids.map((sid) => (
                          <span
                            key={sid}
                            className="px-2 py-0.5 bg-slate-100 rounded text-xs"
                          >
                            {sid}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-slate-400">No services</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => startEditing(group)}
                        className="text-xs text-blue-600 hover:text-blue-700"
                      >
                        Edit Permissions
                      </button>
                      <button
                        onClick={() => handleDeleteGroup(group.group_id, group.name)}
                        className="text-xs text-red-600 hover:text-red-700"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {groups?.length === 0 && (
            <div className="p-8 text-center text-slate-500">No groups</div>
          )}
        </div>
      )}
    </div>
  );
}
