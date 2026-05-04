// Use Next.js proxy to avoid CORS - browser calls /api-proxy/*, Next.js server proxies to API
// The API key is injected server-side by the route handler (app/api-proxy/[...path]/route.ts)
const BASE_URL = "/api-proxy";

function headers(extra?: Record<string, string>) {
  return { "Content-Type": "application/json", ...extra };
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { ...headers(), ...(init?.headers as Record<string, string> | undefined) },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

// ── Types ────────────────────────────────────────────────────────────────────

export interface ProjectContext {
  context_key: string;
  value: unknown;
  description?: string;
  updated_by: string;
  last_updated: string;
  service_id?: string;
  category?: string;
}

export interface Job {
  job_id: string;
  type: string;
  status: string;
  priority: number;
  payload?: unknown;
  result?: any;
  assigned_agent?: string | null;
  created_at: string;
  updated_at?: string;
  notes?: string;
  context_job_ids?: string[];
  skill_key?: string | null;
  created_by?: string;
  depends_on?: string[];
  skill?: any;
  error?: string;
  context_jobs?: Array<{job_id: string; type: string; status: string; result?: any}>;
}

// ── Users / Groups (Admin) ───────────────────────────────────────────────────

export const api = {
  // Users
  listUsers: () => request<any[]>("/admin/users"),
  createUser: (body: { name: string; email?: string; role: string }) =>
    request<{ user_id: string; token: string }>("/admin/users", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  deactivateUser: (userId: string) =>
    fetch(`${BASE_URL}/admin/users/${userId}`, { method: "DELETE", headers: headers() }),
  getUserGroups: (userId: string) =>
    request<any[]>(`/admin/users/${userId}/groups`),
  addUserToGroup: (userId: string, groupId: string) =>
    fetch(`${BASE_URL}/admin/users/${userId}/groups/${groupId}`, { method: "POST", headers: headers() }),
  removeUserFromGroup: (userId: string, groupId: string) =>
    fetch(`${BASE_URL}/admin/users/${userId}/groups/${groupId}`, { method: "DELETE", headers: headers() }),

  // Groups
  listGroups: () => request<any[]>("/admin/groups"),
  createGroup: (body: { name: string; description?: string; allowed_service_ids: string[] }) =>
    request<any>("/admin/groups", { method: "POST", body: JSON.stringify(body) }),
  updateGroup: (groupId: string, body: Partial<{ name: string; description: string; allowed_service_ids: string[] }>) =>
    request<any>(`/admin/groups/${groupId}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteGroup: (groupId: string) =>
    fetch(`${BASE_URL}/admin/groups/${groupId}`, { method: "DELETE", headers: headers() }),

  // MCP Services
  listMCPServices: () => request<any[]>("/mcp/services"),
  registerMCPService: (body: { service_id: string; name: string; endpoint: string; api_key?: string; capabilities?: string[]; protocol?: string }) =>
    request<any>("/mcp/register", { method: "POST", body: JSON.stringify(body) }),
  deleteMCPService: (serviceId: string) =>
    fetch(`${BASE_URL}/mcp/services/${serviceId}`, { method: "DELETE", headers: headers() }),
  sendMCPHeartbeat: (serviceId: string) =>
    request<any>(`/mcp/heartbeat/${serviceId}`, { method: "POST" }),

  // Agents
  listAgents: () => request<any[]>("/agents/"),
  deleteAgent: (agentId: string) =>
    fetch(`${BASE_URL}/agents/${agentId}`, { method: "DELETE", headers: headers() }),

  // Jobs
  listJobs: (params?: { status?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.limit) q.set("limit", String(params.limit));
    const qs = q.toString();
    return request<Job[]>(`/jobs/${qs ? "?" + qs : ""}`);
  },
  createJob: (body: { type: string; payload?: unknown; requirements?: unknown; priority?: string | number; assigned_agent?: string | null; created_by?: string; context_job_ids?: string[]; skill_key?: string | null }) =>
    request<Job>("/jobs", { method: "POST", body: JSON.stringify(body) }),
  forceJobStatus: (jobId: string, status: string) =>
    fetch(`${BASE_URL}/jobs/${jobId}/force-status`, { method: "POST", headers: headers(), body: JSON.stringify({ status }) }),

  // Events / Activity
  listEvents: (params?: { limit?: number; since_id?: number; topic?: string; service_id?: string }) => {
    const q = new URLSearchParams();
    if (params?.limit) q.set("limit", String(params.limit));
    if (params?.since_id) q.set("since_id", String(params.since_id));
    if (params?.topic) q.set("topic", params.topic);
    if (params?.service_id) q.set("service_id", params.service_id);
    const qs = q.toString();
    return request<{count: number; filters: any; events: any[]}>(`/api/event-log${qs ? "?" + qs : ""}`);
  },

  // Context
  listContext: () => request<ProjectContext[]>("/context/"),
  setContext: (key: string, body: { value: unknown; updated_by: string; description?: string; service_id?: string; category?: string }) =>
    request<ProjectContext>(`/context/${encodeURIComponent(key)}`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  deleteContext: (key: string) =>
    request<void>(`/context/${encodeURIComponent(key)}`, { method: "DELETE" }),

  // System
  getSystemState: () => request<any>("/system/state"),

  // Main dashboard stats
  listAgentsForStats: () => request<any[]>("/agents/"),

  // Chat
  listChannels: () => request<any[]>("/chat/channels/"),
  createChannel: (name: string) =>
    request<any>(`/chat/channels/?name=${encodeURIComponent(name)}`, { method: "POST" }),
  getChannelMessages: (channelName: string, limit?: number, beforeId?: number) => {
    const params = new URLSearchParams();
    if (limit) params.set("limit", String(limit));
    if (beforeId) params.set("before_id", String(beforeId));
    const qs = params.toString();
    return request<{messages: any[]; channel: string}>(`/chat/channels/${encodeURIComponent(channelName)}/messages/${qs ? "?" + qs : ""}`);
  },
  postMessage: (channelName: string, sender: string, text: string, msgType?: string, replyTo?: number) => {
    const q = new URLSearchParams({ sender, text, msg_type: msgType || "chat" });
    if (replyTo) q.set("reply_to", String(replyTo));
    return request<any>(`/chat/channels/${encodeURIComponent(channelName)}/messages/?${q}`, { method: "POST" });
  },

  // Agent Spawn
  listAgentCredentials: () => request<any[]>("/agents/credentials/"),
  storeAgentCredential: (agentType: string, apiKey: string) =>
    request<any>("/agents/credentials/", {
      method: "POST",
      body: JSON.stringify({ agent_type: agentType, api_key: apiKey }),
    }),
  deleteAgentCredential: (agentType: string) =>
    fetch(`${BASE_URL}/agents/credentials/${agentType}`, { method: "DELETE", headers: headers() }),
  listSpawnableAgents: () => request<any[]>("/agents/spawnable/"),
  listSpawnedAgents: () => request<any[]>("/agents/spawned/"),
  spawnAgent: (agentType: string, channel: string, task?: string) =>
    request<any>("/agents/spawn/", {
      method: "POST",
      body: JSON.stringify({ agent_type: agentType, channel, task }),
    }),
  killSpawnedAgent: (agentId: string) =>
    fetch(`${BASE_URL}/agents/spawned/${agentId}/`, { method: "DELETE", headers: headers() }),

  // Agent Terminal
  createTerminalToken: (agentId: string) =>
    request<{token: string; expires_in: number; container_id: string}>(`/agents/spawned/${agentId}/terminal-token/`, { method: "POST" }),

  // Jobs
  listChatJobs: (params?: { category?: string; status?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.category) q.set("category", params.category);
    if (params?.status) q.set("status", params.status);
    if (params?.limit) q.set("limit", String(params.limit));
    const qs = q.toString();
    return request<{jobs: any[]; count: number}>(`/chat/jobs/${qs ? "?" + qs : ""}`);
  },
  createChatJob: (body: { title: string; body: string; category: string; channel: string }) =>
    request<any>("/chat/jobs/", { method: "POST", body: JSON.stringify(body) }),
  claimChatJob: (jobId: string) =>
    request<any>(`/chat/jobs/${jobId}/claim/`, { method: "POST" }),
  completeChatJob: (jobId: string, summary: string) =>
    request<any>(`/chat/jobs/${jobId}/done/", { method: "POST", body: JSON.stringify({ summary }) }),

  // Rules
  listRules: (params?: { status?: string; author?: string; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    if (params?.author) q.set("author", params.author);
    if (params?.limit) q.set("limit", String(params.limit));
    const qs = q.toString();
    return request<{rules: any[]; count: number; epoch: number}>(`/rules/${qs ? "?" + qs : ""}`);
  },
  getActiveRules: () => request<{epoch: number; count: number; rules: string[]}>('/rules/active/'),
  createRule: (body: { text: string; author: string; reason?: string }) =>
    request<any>("/rules/", { method: "POST", body: JSON.stringify(body) }),
  activateRule: (ruleId: string) =>
    request<any>(`/rules/${ruleId}/activate/`, { method: "POST" }),
  archiveRule: (ruleId: string) =>
    request<any>(`/rules/${ruleId}/archive/`, { method: "POST" }),
  draftRule: (ruleId: string) =>
    request<any>(`/rules/${ruleId}/draft/`, { method: "POST" }),
  deleteRule: (ruleId: string) =>
    fetch(`${BASE_URL}/rules/${ruleId}/`, { method: "DELETE", headers: headers() }),
};
