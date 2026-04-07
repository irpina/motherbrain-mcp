# Motherbrain MCP — Business Case

## Executive Summary

Motherbrain is an **MCP proxy layer** — it sits between LLMs (Claude, Kimi, and any MCP-compatible client) and the MCP servers in your local environment. It registers as an MCP server itself, so LLMs connect to it like any other tool server. Every tool call the LLM makes flows through Motherbrain, which proxies it to the real service, logs the full interaction, and returns the result — giving administrators complete visibility into how AI models are actually using your tools.

---

## The Core Problem

MCP servers are proliferating. Teams run servers for file access, database queries, web search, code execution, and more. LLMs connect to them and invoke tools — but **nobody sees what's happening**.

> *An LLM calls `read_file("/etc/passwd")` on your local MCP server. Who knows? When? With what result?*

Without a proxy layer, MCP tool usage is a black box. Administrators have no audit trail, no usage analytics, and no way to detect misuse or unexpected behavior from AI models operating in their environment.

---

## What Motherbrain Does

```
LLM (Claude / Kimi / any client)
        │
        │  connects to Motherbrain as an MCP server
        ▼
┌────────────────────────────────┐
│         MOTHERBRAIN            │
│                                │
│  • Receives tool call          │
│  • Logs: who, what, when, args │
│  • Proxies to real MCP server  │
│  • Logs: response, duration    │
│  • Returns result to LLM       │
└────────────┬───────────────────┘
             │  proxies to registered services
     ┌───────┼───────┐
     ▼       ▼       ▼
 agentchattr  DB   filesystem
  (MCP)      (MCP)   (MCP)
```

From the LLM's perspective, Motherbrain *is* the MCP server. It exposes the same tool interface. The LLM calls `call_tool("agentchattr-mcp", "chat_send", {...})` — Motherbrain handles the proxying transparently.

From the administrator's perspective, every single tool call is captured, searchable, and inspectable in a real-time dashboard.

---

## Key Capabilities

### 1. MCP Proxy — Transparent to the LLM
- Register any MCP-compatible server (REST or full JSON-RPC with session handshake)
- LLMs connect to Motherbrain once and reach all registered services through it
- Supports the full MCP protocol (initialize → notifications/initialized → tools/call)
- Service registry with online/offline status and capability discovery

### 2. Full Audit Trail — Every Tool Call Logged
- Persistent PostgreSQL log of every tool invocation
- Captures: timestamp, topic, service, tool name, calling agent, arguments, full response, duration, status
- Survives server restarts — no in-memory-only audit trail
- Queryable by service, tool, agent, topic, or time window

### 3. Real-Time Admin Dashboard
- Live activity feed showing all MCP tool calls as they happen (3-second polling)
- Filter by topic (chat, proxy, system), service, or agent
- Click any event to expand full argument and response JSON
- Agent panel showing registered LLM clients with tiered presence (Active / Idle / Away)

### 4. Agent Identity Management
- LLM clients register with a human-readable name and hostname (`claude @ dev-machine`)
- Idempotent re-registration — reconnecting clients reclaim their identity and get a fresh token
- Multiple instances of the same agent type coexist without collision (`kimi @ alice-box` vs `kimi @ bob-server`)
- SHA-256 token hashing — no plaintext credentials stored anywhere

### 5. Job Orchestration (Secondary)
- Create and route work to registered agents or MCP services
- Full job lifecycle: pending → running → completed/failed
- Priority queuing via Redis (atomic dequeue — no double-claiming)
- Shared context/skill store accessible to all connected agents

---

## Why This Matters

### For Security Teams
You cannot govern what you cannot see. Motherbrain creates the visibility layer that makes LLM tool usage auditable. Every `read_file`, `execute_code`, or `query_database` call is logged with full context — what the LLM sent and what it got back.

### For Platform/DevOps Teams
One registration point for all MCP services. Add a new tool server once; all connected LLMs can reach it through Motherbrain. Monitor service health, detect failures, and see usage patterns without instrumenting each service individually.

### For Compliance
The event log provides the immutable record required by AI governance frameworks: which model invoked which tool, with what arguments, at what time, and what data was returned. This is the foundation for AI access control policies and regulatory reporting.

### For Developers
A local Motherbrain instance gives you a complete picture of how your LLM integrations behave in practice — what tools get called most, what arguments the model generates, where failures occur. Far more informative than reading LLM output alone.

---

## Technical Architecture

| Layer | Technology |
|-------|-----------|
| Proxy / API | FastAPI (async) |
| MCP protocol | FastMCP (streamable-http transport) |
| Audit database | PostgreSQL + SQLAlchemy 2.0 async |
| Job queue | Redis (atomic LPOP) |
| Dashboard | Next.js + Tailwind CSS |
| Auth | SHA-256 token hashing per agent |
| Deployment | Docker Compose (single command) |

**Motherbrain exposes `/mcp` as a standard MCP endpoint.** LLMs configure it as an MCP server URL — no custom client code needed. The proxy handles all session management and protocol negotiation internally.

---

## Current State

| Component | Status |
|-----------|--------|
| MCP proxy (REST + JSON-RPC) | ✅ Live |
| Persistent event log with full call details | ✅ Live |
| Real-time dashboard with click-to-expand | ✅ Live |
| Agent identity (named, hostname-scoped) | ✅ Live |
| SHA-256 token security | ✅ Live |
| Job orchestration + lifecycle | ✅ Live |
| Tiered presence model | ✅ Live |
| Job retry / circuit breaker | 📋 Planned |
| WebSocket real-time push | 📋 Planned |

---

