"use client";

import { api } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { formatRelativeTime, getTopicBadgeColor, getStatusBadgeColor } from "@/lib/utils";
import { useState, useMemo, Fragment } from "react";
import { ChevronRight, ChevronDown, Loader2, AlertCircle } from "lucide-react";

const ALL_TOPICS = ["chat", "heartbeat", "proxy", "system"];

export function ActivityFeed({ limit = 100 }: { limit?: number }) {
  const [search, setSearch] = useState("");
  const [selectedTopics, setSelectedTopics] = useState<Set<string>>(new Set());
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["events", limit],
    queryFn: () => api.listEvents({ limit }),
    refetchInterval: 3000,
  });

  const toggleTopic = (t: string) => {
    setSelectedTopics(prev => {
      const next = new Set(prev);
      next.has(t) ? next.delete(t) : next.add(t);
      return next;
    });
  };

  const filtered = useMemo(() => {
    if (!data?.events) return [];
    return data.events.filter(e => {
      const matchesTopic = selectedTopics.size === 0 || selectedTopics.has(e.topic);
      const q = search.toLowerCase();
      const matchesSearch = !q || [e.topic, e.service_id, e.tool_name, e.status, e.agent_id].some(
        v => v?.toLowerCase().includes(q)
      );
      return matchesTopic && matchesSearch;
    });
  }, [data, search, selectedTopics]);

  return (
    <div className="bg-elevated rounded-lg border border-border overflow-hidden">
      <div className="px-4 py-3 border-b border-border bg-subtle space-y-2.5">
        <div className="flex items-center gap-2">
          <h2 className="font-medium text-[15px]">Activity Log</h2>
          <span className="ml-auto text-xs text-muted-foreground">
            {filtered.length} / {data?.count ?? 0} events
          </span>
        </div>
        {/* Search bar */}
        <input
          type="text"
          placeholder="Search by service, tool, status, agent..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full px-3 py-1.5 text-sm bg-input border border-border rounded-md text-primary placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent/50 focus:border-accent/50"
        />
        {/* Topic chips */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-muted-foreground">Filter:</span>
          {ALL_TOPICS.map(t => (
            <button
              key={t}
              onClick={() => toggleTopic(t)}
              className={`px-2.5 py-0.5 rounded-full text-xs border transition-colors ${
                selectedTopics.has(t)
                  ? "bg-accent text-white border-accent"
                  : "bg-elevated text-muted-foreground border-border hover:border-muted-foreground/50"
              }`}
            >
              {t}
            </button>
          ))}
          {selectedTopics.size > 0 && (
            <button
              onClick={() => setSelectedTopics(new Set())}
              className="text-xs text-muted-foreground hover:text-primary ml-1 transition-colors"
            >
              clear
            </button>
          )}
        </div>
      </div>
      <div className="max-h-[600px] overflow-y-auto">
        {isLoading && (
          <div className="p-8 flex items-center justify-center text-muted-foreground gap-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading events...
          </div>
        )}
        {isError && (
          <div className="p-8 flex items-center justify-center text-muted-foreground gap-2 text-sm">
            <AlertCircle className="w-4 h-4 text-destructive" />
            Could not load events — is the API reachable?
          </div>
        )}
        {!isLoading && !isError && filtered.length === 0 && (
          <div className="p-8 text-center text-muted-foreground text-sm">
            <p className="font-medium text-primary mb-1">
              {search || selectedTopics.size > 0 ? "No matching events" : "No events yet"}
            </p>
            <p className="text-xs">
              {search || selectedTopics.size > 0
                ? "Try clearing filters to see more results."
                : "Events are logged automatically when agents call MCP tools."}
            </p>
          </div>
        )}
        {!isLoading && !isError && filtered.length > 0 && (
          <table className="w-full text-sm">
            <thead className="bg-elevated text-muted-foreground sticky top-0 border-b border-border">
              <tr>
                <th className="px-4 py-2 text-left font-medium w-8"></th>
                <th className="px-4 py-2 text-left font-medium">Time</th>
                <th className="px-4 py-2 text-left font-medium">Topic</th>
                <th className="px-4 py-2 text-left font-medium">Service</th>
                <th className="px-4 py-2 text-left font-medium">Agent</th>
                <th className="px-4 py-2 text-left font-medium">Tool</th>
                <th className="px-4 py-2 text-left font-medium">Status</th>
                <th className="px-4 py-2 text-left font-medium">ms</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map((event) => (
                <Fragment key={event.id}>
                  <tr
                    onClick={() => setExpandedId(expandedId === event.id ? null : event.id)}
                    className="hover:bg-subtle/50 cursor-pointer transition-colors"
                  >
                    <td className="px-4 py-2 text-muted-foreground">
                      {expandedId === event.id ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </td>
                    <td className="px-4 py-2 text-muted-foreground whitespace-nowrap text-xs">
                      {formatRelativeTime(event.timestamp)}
                    </td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-0.5 rounded text-xs ${getTopicBadgeColor(event.topic)}`}>
                        {event.topic}
                      </span>
                    </td>
                    <td className="px-4 py-2 font-mono text-xs text-muted-foreground">{event.service_id}</td>
                    <td className="px-4 py-2 font-mono text-xs text-muted-foreground">{event.agent_id ?? "—"}</td>
                    <td className="px-4 py-2 font-mono text-xs text-primary">{event.tool_name}</td>
                    <td className="px-4 py-2">
                      <span className={`px-2 py-0.5 rounded text-xs ${getStatusBadgeColor(event.status)}`}>
                        {event.status}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-muted-foreground text-xs">{event.duration_ms}</td>
                  </tr>
                  {expandedId === event.id && (
                    <tr className="bg-subtle/40">
                      <td colSpan={8} className="px-4 py-3 text-xs">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <div className="font-medium text-muted-foreground mb-1">Agent</div>
                            <div className="font-mono text-muted-foreground">{event.agent_id ?? "—"}</div>
                            <div className="font-medium text-muted-foreground mt-3 mb-1">Arguments</div>
                            <pre className="bg-elevated border border-border rounded-md p-3 overflow-auto max-h-40 text-primary">
                              {JSON.stringify(event.arguments, null, 2)}
                            </pre>
                          </div>
                          <div>
                            <div className="font-medium text-muted-foreground mb-1">Response</div>
                            <pre className="bg-elevated border border-border rounded-md p-3 overflow-auto max-h-48 text-primary">
                              {JSON.stringify(event.response, null, 2)}
                            </pre>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
