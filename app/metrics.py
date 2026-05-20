"""Prometheus metrics for Motherbrain.

Custom metrics beyond the standard HTTP instrumentation:
- Proxy call counts and latency per service/tool/status
- Online service and agent gauges (updated by background tasks)
"""

from prometheus_client import Counter, Histogram, Gauge

proxy_calls_total = Counter(
    "motherbrain_proxy_calls_total",
    "Total MCP proxy calls dispatched",
    ["service_id", "tool_name", "status"],
)

proxy_latency_seconds = Histogram(
    "motherbrain_proxy_latency_seconds",
    "MCP proxy call latency",
    ["service_id", "tool_name"],
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

services_online = Gauge(
    "motherbrain_services_online",
    "Number of MCP services currently marked online",
)

agents_online = Gauge(
    "motherbrain_agents_online",
    "Number of agents with a heartbeat in the last 5 minutes",
)
