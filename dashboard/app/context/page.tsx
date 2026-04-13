"use client";

import { useState, useMemo } from "react";
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
      <td className="px-4 py-3" colSpan={7}>
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
            {/* RBAC indicators */}
            {ctx.service_id && (
              <span className="px-2 py-0.5 bg-amber-100 text-amber-800 rounded text-xs" title="Restricted to users with permission on this service">
                🔒 {ctx.service_id}
              </span>
            )}
            {ctx.category && (
              <span className="px-2 py-0.5 bg-purple-100 text-purple-800 rounded text-xs">
                📁 {ctx.category}
              </span>
            )}
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

function ContextRow({ ctx, editing, editValue, editServiceId, editCategory, onEdit, onSave, onCancel, onDelete, onEditChange, onServiceIdChange, onCategoryChange }: {
  ctx: ProjectContext;
  editing: boolean;
  editValue: string;
  editServiceId: string;
  editCategory: string;
  onEdit: () => void;
  onSave: () => void;
  onCancel: () => void;
  onDelete: () => void;
  onEditChange: (v: string) => void;
  onServiceIdChange: (v: string) => void;
  onCategoryChange: (v: string) => void;
}) {
  return (
    <tr className="hover:bg-slate-50">
      <td className="px-4 py-3 font-mono text-sm">
        {ctx.context_key}
        {/* RBAC indicators */}
        <div className="flex gap-1 mt-1">
          {ctx.service_id && (
            <span className="px-1.5 py-0.5 bg-amber-100 text-amber-800 rounded text-[10px]" title="Restricted to users with permission on this service">
              🔒 {ctx.service_id}
            </span>
          )}
          {ctx.category && (
            <span className="px-1.5 py-0.5 bg-purple-100 text-purple-800 rounded text-[10px]">
              📁 {ctx.category}
            </span>
          )}
        </div>
      </td>
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
          <div className="space-y-2">
            <input
              type="text"
              value={editServiceId}
              onChange={(e) => onServiceIdChange(e.target.value)}
              placeholder="Service ID (optional)"
              className="w-full px-2 py-1 border rounded text-xs"
            />
            <input
              type="text"
              value={editCategory}
              onChange={(e) => onCategoryChange(e.target.value)}
              placeholder="Category (optional)"
              className="w-full px-2 py-1 border rounded text-xs"
            />
            <div className="flex gap-2">
              <button onClick={onSave} className="text-green-600 hover:underline text-xs">Save</button>
              <button onClick={onCancel} className="text-slate-500 hover:underline text-xs">Cancel</button>
            </div>
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
  const [editServiceId, setEditServiceId] = useState("");
  const [editCategory, setEditCategory] = useState("");
  const [newKey, setNewKey] = useState("");
  const [newValue, setNewValue] = useState("{}");
  const [newDescription, setNewDescription] = useState("");
  const [newServiceId, setNewServiceId] = useState("");
  const [newCategory, setNewCategory] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  const [showSkillsOnly, setShowSkillsOnly] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState<string>("all");

  const { data: contexts, isLoading } = useQuery({
    queryKey: ["context"],
    queryFn: api.listContext,
    refetchInterval: 5000,
  });

  // Get unique categories for filter dropdown
  const categories = useMemo(() => {
    if (!contexts) return [];
    const cats = new Set<string>();
    contexts.forEach(c => {
      if (c.category) cats.add(c.category);
    });
    return Array.from(cats).sort();
  }, [contexts]);

  const filteredContexts = useMemo(() => {
    let result = contexts;
    
    // Skills filter
    if (showSkillsOnly) {
      result = result?.filter(c => c.context_key.startsWith("skills."));
    }
    
    // Category filter
    if (categoryFilter !== "all") {
      result = result?.filter(c => c.category === categoryFilter);
    }
    
    return result;
  }, [contexts, showSkillsOnly, categoryFilter]);

  const handleEdit = (ctx: ProjectContext) => {
    setEditingKey(ctx.context_key);
    setEditValue(JSON.stringify(ctx.value, null, 2));
    setEditServiceId(ctx.service_id || "");
    setEditCategory(ctx.category || "");
  };

  const handleSave = async (key: string) => {
    try {
      const parsed = JSON.parse(editValue);
      await api.setContext(key, {
        value: parsed,
        updated_by: "dashboard",
        service_id: editServiceId || undefined,
        category: editCategory || undefined,
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
        service_id: newServiceId || undefined,
        category: newCategory || undefined,
      });
      queryClient.invalidateQueries({ queryKey: ["context"] });
      setIsAdding(false);
      setNewKey("");
      setNewValue("{}");
      setNewDescription("");
      setNewServiceId("");
      setNewCategory("");
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
          <p className="text-slate-500">Shared key-value store for agents with RBAC</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Category filter */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-2 border rounded-md text-sm"
          >
            <option value="all">All Categories</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          
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
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Service ID (optional)
                <span className="text-slate-400 font-normal ml-1">— Restrict to users with permission</span>
              </label>
              <input
                type="text"
                value={newServiceId}
                onChange={(e) => setNewServiceId(e.target.value)}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="e.g., agentchattr-mcp"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Category (optional)
                <span className="text-slate-400 font-normal ml-1">— For UI organization</span>
              </label>
              <input
                type="text"
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                className="w-full px-3 py-2 border rounded-md"
                placeholder="e.g., devops, onboarding"
              />
            </div>
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
                <th className="px-4 py-3 text-left font-medium" colSpan={7}>
                  Skills ({filteredContexts?.length || 0})
                  {categoryFilter !== "all" && (
                    <span className="ml-2 text-slate-400 font-normal">
                      — filtered by category: {categoryFilter}
                    </span>
                  )}
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
                  editServiceId={editServiceId}
                  editCategory={editCategory}
                  onEdit={() => handleEdit(ctx)}
                  onSave={() => handleSave(ctx.context_key)}
                  onCancel={() => setEditingKey(null)}
                  onDelete={() => handleDelete(ctx.context_key)}
                  onEditChange={setEditValue}
                  onServiceIdChange={setEditServiceId}
                  onCategoryChange={setEditCategory}
                />
              );
            })}
          </tbody>
        </table>
        {filteredContexts?.length === 0 && (
          <div className="p-8 text-center text-slate-500">
            {showSkillsOnly ? "No skills found" : "No context keys"}
            {categoryFilter !== "all" && " in this category"}
          </div>
        )}
      </div>
    </div>
  );
}
