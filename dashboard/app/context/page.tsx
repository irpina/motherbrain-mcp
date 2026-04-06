"use client";

import { useState } from "react";
import { api, type ProjectContext } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { formatRelativeTime } from "@/lib/utils";

export default function ContextPage() {
  const queryClient = useQueryClient();
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [newKey, setNewKey] = useState("");
  const [newValue, setNewValue] = useState("{}");
  const [newDescription, setNewDescription] = useState("");
  const [isAdding, setIsAdding] = useState(false);

  const { data: contexts, isLoading } = useQuery({
    queryKey: ["context"],
    queryFn: api.listContext,
    refetchInterval: 5000,
  });

  const handleEdit = (ctx: ProjectContext) => {
    setEditingKey(ctx.context_key);
    setEditValue(JSON.stringify(ctx.value, null, 2));
  };

  const handleSave = async (key: string) => {
    try {
      const parsed = JSON.parse(editValue);
      await api.setContext(key, {
        value: parsed,
        updated_by: "dashboard",
      });
      queryClient.invalidateQueries({ queryKey: ["context"] });
      setEditingKey(null);
    } catch (e) {
      alert("Invalid JSON: " + (e as Error).message);
    }
  };

  const handleDelete = async (key: string) => {
    if (!confirm(`Delete key "${key}"?`)) return;
    await api.deleteContext(key);
    queryClient.invalidateQueries({ queryKey: ["context"] });
  };

  const handleAdd = async () => {
    try {
      const parsed = JSON.parse(newValue);
      await api.setContext(newKey, {
        value: parsed,
        updated_by: "dashboard",
        description: newDescription || undefined,
      });
      queryClient.invalidateQueries({ queryKey: ["context"] });
      setIsAdding(false);
      setNewKey("");
      setNewValue("{}");
      setNewDescription("");
    } catch (e) {
      alert("Invalid JSON: " + (e as Error).message);
    }
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Project Context</h1>
          <p className="text-slate-500">Shared key-value store for agents</p>
        </div>
        <button
          onClick={() => setIsAdding(true)}
          className="px-4 py-2 bg-slate-900 text-white rounded-md hover:bg-slate-800"
        >
          Add Key
        </button>
      </div>

      {isAdding && (
        <div className="bg-white p-4 rounded-lg border shadow-sm space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Key</label>
            <input
              type="text"
              value={newKey}
              onChange={(e) => setNewKey(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
              placeholder="e.g., config.api_url"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Value (JSON)</label>
            <textarea
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border rounded-md font-mono text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Description</label>
            <input
              type="text"
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setIsAdding(false)}
              className="px-4 py-2 border rounded-md hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              onClick={handleAdd}
              className="px-4 py-2 bg-slate-900 text-white rounded-md hover:bg-slate-800"
            >
              Save
            </button>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Key</th>
              <th className="px-4 py-3 text-left font-medium">Value</th>
              <th className="px-4 py-3 text-left font-medium">Updated By</th>
              <th className="px-4 py-3 text-left font-medium">Last Updated</th>
              <th className="px-4 py-3 text-left font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {contexts?.map((ctx) => (
              <tr key={ctx.context_key} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-mono text-sm">{ctx.context_key}</td>
                <td className="px-4 py-3">
                  {editingKey === ctx.context_key ? (
                    <textarea
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      rows={4}
                      className="w-full px-2 py-1 border rounded font-mono text-xs"
                    />
                  ) : (
                    <pre className="text-xs bg-slate-100 p-2 rounded overflow-x-auto">
                      {JSON.stringify(ctx.value, null, 2)}
                    </pre>
                  )}
                </td>
                <td className="px-4 py-3">{ctx.updated_by}</td>
                <td className="px-4 py-3 text-slate-500">
                  {formatRelativeTime(ctx.last_updated)}
                </td>
                <td className="px-4 py-3">
                  {editingKey === ctx.context_key ? (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleSave(ctx.context_key)}
                        className="text-green-600 hover:underline text-xs"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setEditingKey(null)}
                        className="text-slate-500 hover:underline text-xs"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEdit(ctx)}
                        className="text-blue-600 hover:underline text-xs"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(ctx.context_key)}
                        className="text-red-600 hover:underline text-xs"
                      >
                        Delete
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {contexts?.length === 0 && (
          <div className="p-8 text-center text-slate-500">No context keys</div>
        )}
      </div>
    </div>
  );
}
