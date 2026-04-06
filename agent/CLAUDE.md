# Agent — Example Agent Implementation

## Purpose
Reference implementation showing how agents interact with Motherbrain.

## Structure

```
agent/
├── agent.py          # Full agent implementation
└── CLAUDE.md         # This file
```

## Agent Lifecycle

```
1. REGISTER → POST /agents/register
   ← Receive agent_id and token

2. HEARTBEAT (every 10s) → POST /agents/heartbeat
   ← 200 OK

3. POLL FOR JOBS → GET /jobs/next
   ← Job or 204 No Content

4. EXECUTE JOB → Run task locally
   
5. UPDATE STATUS → POST /jobs/{id}/status
   ← 200 OK

6. REPEAT from step 2
```

## Key Concepts

### Authentication

Agents use **token-based auth** after registration:

```python
headers = {"X-Agent-Token": self.token}
response = httpx.get(f"{API_URL}/jobs/next", headers=headers)
```

### Capabilities

Agents declare what they can do:

```python
capabilities = {
    "code_generation": True,
    "python": True,
    "fastapi": True
}
```

Jobs specify requirements that must match:

```python
requirements = ["code_generation", "python"]
```

### Polling Strategy

The example uses simple polling with `time.sleep()`. For production:
- Use async/await for concurrent operations
- Implement exponential backoff on errors
- Add circuit breaker for API failures

## Creating a Custom Agent

1. Copy `agent.py` as template
2. Modify `capabilities` to match your agent's skills
3. Implement `execute_job()` for your domain
4. Set environment variables:
   ```bash
   export MOTHERBRAIN_API_URL=http://localhost:8000
   export MOTHERBRAIN_API_KEY=supersecret
   export PLATFORM=my-agent
   ```

## Agent Types

| Type | Capabilities | Use Case |
|------|--------------|----------|
| Code Agent | `code_generation`, `python`, `javascript` | Writing code |
| Review Agent | `code_review`, `architecture` | Reviewing PRs |
| Test Agent | `testing`, `pytest` | Running tests |
| MCP Agent | `mcp_tools` | Tool execution |

## Extension Points

**Safe to modify:**
- `execute_job()` — implement your task logic
- `capabilities` — add new skills
- Polling interval
- Error handling

**Keep as-is:**
- Registration flow
- Authentication headers
- Status update format
