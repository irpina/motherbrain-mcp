"use client";

import { useState } from "react";
import { api, type ProjectContext } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { formatRelativeTime } from "@/lib/utils";

interface SkillValue {
  prompt?: string;
  tags?: string[];
  version?: string;
}

function isSkillValue(value: unknown): value is SkillValue {
  return typeof value === "object" && value !== null && "prompt" in value;
}

function SkillRow({ ctx, onEdit, onDelete }: { 
  ctx: ProjectContext; 
  onEdit: () => void;
  onDelete: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const skill = ctx.value as SkillValue;
  const tags = skill.tags || [];
  const version = skill.version || "v1.0";
  const prompt = skill.prompt || "";
  
  const truncatedPrompt = prompt.length > 120 && !expanded 
    ? prompt.slice(0, 120) + "..." 
    : prompt;

  return (
    <tr className="hover:bg-slate-50">
      <td className="px-4 py-3" colSpan={5}>
        <div className="space-y-2">
          {/* Header row */}
          <div className="flex items-center gap-3 flex-wrap">
            <span className="font-mono text-sm font-medium">{ctx.context_key}</span>
            <span className="text-xs text-slate-400">•</span>
            {tags.map(tag => (
              <span key={tag} className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs">
                {tag}
              </span>
            ))}
            <span className="px-2 py-0.5 bg-slate-200 text-slate-700 rounded text-xs">
              {version}
            </span>
            <span className="text-xs text-slate-400 ml-auto">
              {ctx.updated_by} • {formatRelativeTime(ctx.last_updated)}
            </span>
            <button onClick={onEdit} className="text-blue-600 hover:underline text-xs">
              Edit
            </button>
            <button onClick={onDelete} className="text-red-600 hover:underline text-xs">
              Delete
            </button>
          </div>
          {/* Prompt */}
          <div className="text-sm text-slate-700 bg-slate-50 p-3 rounded">
            {truncatedPrompt}
            {prompt.length > 120 && (
              <button 
                onClick={() => setExpanded(!expanded)}
                className="text-blue-600 hover:underline text-xs ml-2"
              >
                {expanded ? "show less" : "show more"}
              </button>
            )}
          </div>
        </div>
      </td>
    </tr>
  );
}

function ContextRow({ ctx, editing, editValue, onEdit, onSave, onCancel, onDelete, onEditChange }: {
  ctx: ProjectContext;
  editing: boolean;
  editValue: string;
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  onDelete: () => void;
  onEditChange: (v: string) => void;
}) {
  return (
    <tr className="hover:bg-slate-50">
      <td className="px-4 py-3 font-mono text-sm">{ctx.context_key}</td>
      <td className="px-4 py-3">
        {editing ? (
          <textarea
            value={editValue}
            onChange={(e) => onEditChange(e.target.value)}
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
        {editing ? (
          <div className="flex gap-2">
            <button onClick={onSave} className="text-green-600 hover:underline text-xs">Save</button>
            <button onClick={onCancel} className="text-slate-500 hover:underline text-xs">Cancel</button>
          </div>
        ) : (
          <div className="flex gap-2">
            <button onClick={onEdit} className="text-blue-600 hover:underline text-xs">Edit</button>
            <button onClick={onDelete} className="text-red-600 hover:underline text-xs">Delete</button>
          </div>
        )}
      </td>
    </tr>
  );
}

export default function ContextPage() {
  const queryClient = useQueryClient();
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [newKey, setNewKey] = useState("");
  const [newValue, setNewValue] = useState("{}");
  const [newDescription, setNewDescription] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  const [showSkillsOnly, setShowSkillsOnly] = useState(false);

  const { data: contexts, isLoading } = useQuery({
    queryKey: ["context"],
    queryFn: api.listContext,
    refetchInterval: 5000,
  });

  const filteredContexts = showSkillsOnly
    ? contexts?.filter(c => c.context_key.startsWith("skills."))
    : contexts;

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
        <div className="flex items-center gap-3">
          {/* Skills filter toggle */}
          <button
            onClick={() => setShowSkillsOnly(!showSkillsOnly)}
            className={`px-4 py-2 rounded-md text-sm border transition-colors ${
              showSkillsOnly
                ? "bg-blue-600 text-white border-blue-600"
                : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
            }`}
          >
            {showSkillsOnly ? "Showing Skills" : "Show All"}
          </button>
          <button
            onClick={() => setIsAdding(true)}
            className="px-4 py-2 bg-slate-900 text-white rounded-md hover:bg-slate-800"
          >
            Add Key
          </button>
        </div>
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
              placeholder="e.g., skills.my_skill or config.api_url"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Value (JSON)</label>
            <textarea
              value={newValue}
              onChange={(e) => setNewValue(e.target.value)}
              rows={6}
              className="w-full px-3 py-2 border rounded-md font-mono text-sm"
              placeholder='{"prompt": "...", "tags": ["tag1"], "version": "v1.0"}'
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
            {!showSkillsOnly && (
              <tr>
                <th className="px-4 py-3 text-left font-medium">Key</th>
                <th className="px-4 py-3 text-left font-medium">Value</th>
                <th className="px-4 py-3 text-left font-medium">Updated By</th>
                <th className="px-4 py-3 text-left font-medium">Last Updated</th>
                <th className="px-4 py-3 text-left font-medium">Actions</th>
              </tr>
            )}
            {showSkillsOnly && (
              <tr>
                <th className="px-4 py-3 text-left font-medium" colSpan={5}>
                  Skills ({filteredContexts?.length || 0})
                </th>
              </tr>
            )}
          </thead>
          <tbody className="divide-y">
            {filteredContexts?.map((ctx) => {
              const isSkill = ctx.context_key.startsWith("skills.");
              
              if (isSkill && showSkillsOnly) {
                return (
                  <SkillRow
                    key={ctx.context_key}
                    ctx={ctx}
                    onEdit={() => handleEdit(ctx)}
                    onDelete={() => handleDelete(ctx.context_key)}
                  />
                );
              }
              
              return (
                <ContextRow
                  key={ctx.context_key}
                  ctx={ctx}
                  editing={editingKey === ctx.context_key}
                  editValue={editValue}
                  onEdit={() => handleEdit(ctx)}
                  onSave={() => handleSave(ctx.context_key)}
                  onCancel={() => setEditingKey(null)}
                  onDelete={() => handleDelete(ctx.context_key)}
                  onEditChange={setEditValue}
                />
              );
            })}
          </tbody>
        </table>
        {filteredContexts?.length === 0 && (
          <div className="p-8 text-center text-slate-500">
            {showSkillsOnly ? "No skills found" : "No context keys"}
          </div>
        )}
      </div>
    </div>
  );
}
