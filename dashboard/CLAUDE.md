# Dashboard -- Next.js Frontend

## Purpose
Admin UI for the motherbrain control plane. Real-time visibility into
agents, jobs, context, and chat channels.

## Stack

- **Next.js 15** (App Router, `output: standalone`)
- **React Query** (`@tanstack/react-query`) for data fetching
- **Tailwind CSS** + shadcn/ui components
- **TypeScript** strict mode

## Structure

```
dashboard/
├── app/
│   ├── layout.tsx              # Root layout (nav, providers)
│   ├── page.tsx                # Dashboard home (stats)
│   ├── agents/page.tsx         # Agent list + spawn UI
│   ├── jobs/page.tsx           # Job queue management
│   ├── chat/page.tsx           # Real-time chat channels
│   ├── context/page.tsx        # Shared context KV store
│   ├── mcp/page.tsx            # MCP service registry
│   ├── admin/
│   │   ├── groups/page.tsx     # Agent groups
│   │   └── settings/page.tsx  # API key management
│   └── api-proxy/[...path]/
│       └── route.ts            # Server-side proxy to API
├── components/
│   ├── nav.tsx                 # Navigation sidebar
│   ├── agents-panel.tsx        # Agent list component
│   ├── jobs-panel.tsx          # Job list component
│   ├── spawn-agent-dialog.tsx  # Spawn modal
│   ├── spawned-agents-panel.tsx # Running spawned agents
│   └── ...
└── lib/
    ├── api.ts                  # All API calls (BASE_URL = "/api-proxy")
    └── utils.ts                # cn(), formatRelativeTime(), etc.
```

## API Proxy Architecture

All API calls go through the server-side route handler, not directly to port 8000.
This eliminates CORS entirely -- the browser only ever talks to port 3000.

```
Browser -> GET /api-proxy/agents/
        -> Next.js route.ts handler
        -> reads process.env.API_KEY, injects X-API-Key header
        -> fetch("http://api:8000/agents/")
        -> returns response to browser
```

**Critical**: `fetch()` does not support WebSocket protocol upgrades.
WebSocket connections use the token-exchange pattern instead (see below).

**`skipTrailingSlashRedirect: true`** in `next.config.ts` prevents Next.js from
stripping trailing slashes before the route handler runs. FastAPI requires trailing
slashes on list endpoints (`/agents/`, not `/agents`).

## Chat Page WebSocket Flow

1. Load history: `GET /api-proxy/chat/channels/{name}/messages/`
2. Acquire WS token: `POST /api-proxy/chat/ws-token/` -> `{token, expires_in: 60}`
3. Open WebSocket **directly** to API: `ws://host:8000/chat/ws/channels/{name}?token={token}`
4. Send messages: `POST /api-proxy/chat/channels/{name}/messages/?sender=...&text=...`

The WebSocket bypasses the proxy because fetch() cannot handle WS upgrades.
The token (60s TTL, single-use) is issued via the proxy which validates the API key.

## API Client (`lib/api.ts`)

All methods use the `request<T>()` helper:
- Prepends `BASE_URL = "/api-proxy"`
- Adds `X-API-Key` header (injected server-side by route.ts -- not from browser env)
- Throws on non-OK responses

List endpoints need trailing slashes to match FastAPI routes:
`/agents/`, `/jobs/`, `/context/`, `/chat/channels/` etc.

## Adding a New Page

1. Create `dashboard/app/{name}/page.tsx` with `"use client"` at top
2. Use `useQuery` from `@tanstack/react-query` for data
3. Add API method to `lib/api.ts`
4. Add nav link to `components/nav.tsx`

## TypeScript Gotchas

- `Array.some()` on an optional array returns `boolean | undefined` -- add `?? false`
- `ctx: Context` (no default) must come BEFORE parameters with defaults in
  FastMCP `@mcp.tool()` functions (Python syntax requirement)
- Use `any[]` for API response arrays when shape is not statically known

## Build Notes

The dashboard is built at Docker image build time (standalone output).
`API_KEY` is NOT a build-time var -- the route handler reads it at request time.
Changing `API_KEY` in `.env` only requires `docker compose up -d` (not `--build`).
