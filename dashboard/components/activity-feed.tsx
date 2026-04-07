"use client";

import { api } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { formatRelativeTime } from "@/lib/utils";
import { useState, useMemo, Fragment } from "react";
import { ChevronRight, ChevronDown } from "lucide-react";

const ALL_TOPICS = ["chat", "heartbeat", "proxy", "system"];

const topicColors: Record<string, string> = {
  chat: "bg-blue-100 text-blue-800",
  heartbeat: "bg-green-100 text-green-800",
  proxy: "bg-purple-100 text-purple-800",
  system: "bg-slate-100 text-slate-800",
};

export function ActivityFeed({ limit = 100 }: { limit?: number }) {
  const [search, setSearch] = useState("");
  const [selectedTopics, setSelectedTopics] = useState<Set<string>>(new Set());
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const { data, isLoading } = useQuery({
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
    <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b bg-slate-50 space-y-2">
        <div className="flex items-center gap-2">
          <h2 className="font-semibold">Activity Log</h2>
          <span className="ml-auto text-xs text-slate-400">
            {filtered.length} / {data?.count ?? 0} events
          </span>
        </div>
        {/* Search bar */}
        <input
          type="text"
          placeholder="Search by service, tool, status, agent..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full px-3 py-1.5 text-sm border rounded bg-white focus:outline-none focus:ring-1 focus:ring-slate-400"
        />
        {/* Topic chips */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-slate-500">Filter:</span>
          {ALL_TOPICS.map(t => (
            <button
              key={t}
              onClick={() => toggleTopic(t)}
              className={`px-2 py-0.5 rounded-full text-xs border transition-colors ${
                selectedTopics.has(t)
                  ? "bg-slate-800 text-white border-slate-800"
                  : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
              }`}
            >
              {t}
            </button>
          ))}
          {selectedTopics.size > 0 && (
            <button
              onClick={() => setSelectedTopics(new Set())}
              className="text-xs text-slate-400 hover:text-slate-600 ml-1"
            >
              clear
            </button>
          )}
        </div>
      </div>
      <div className="max-h-[600px] overflow-y-auto">
        {isLoading && <div className="p-4 text-slate-500">Loading...</div>}
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-600 sticky top-0">
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
          <tbody className="divide-y">
            {filtered.map((event) => (
              <Fragment key={event.id}>
                <tr
                  onClick={() => setExpandedId(expandedId === event.id ? null : event.id)}
                  className="hover:bg-slate-50 cursor-pointer"
                >
                  <td className="px-4 py-2 text-slate-400">
                    {expandedId === event.id ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                  </td>
                  <td className="px-4 py-2 text-slate-500 whitespace-nowrap">
                    {formatRelativeTime(event.timestamp)}
                  </td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${topicColors[event.topic] ?? "bg-slate-100 text-slate-700"}`}>
                      {event.topic}
                    </span>
                  </td>
                  <td className="px-4 py-2 font-mono text-xs text-slate-600">{event.service_id}</td>
                  <td className="px-4 py-2 font-mono text-xs text-slate-500">{event.agent_id ?? "—"}</td>
                  <td className="px-4 py-2 font-mono text-xs">{event.tool_name}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${event.status === "ok" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                      {event.status}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-slate-400 text-xs">{event.duration_ms}</td>
                </tr>
                {expandedId === event.id && (
                  <tr key={`${event.id}-detail`} className="bg-slate-50">
                    <td colSpan={8} className="px-4 py-3 text-xs">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <div className="font-semibold text-slate-600 mb-1">Agent</div>
                          <div className="font-mono text-slate-500">{event.agent_id ?? "—"}</div>
                          <div className="font-semibold text-slate-600 mt-2 mb-1">Arguments</div>
                          <pre className="bg-white border rounded p-2 overflow-auto max-h-40 text-slate-700">
                            {JSON.stringify(event.arguments, null, 2)}
                          </pre>
                        </div>
                        <div>
                          <div className="font-semibold text-slate-600 mb-1">Response</div>
                          <pre className="bg-white border rounded p-2 overflow-auto max-h-48 text-slate-700">
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
        {filtered.length === 0 && !isLoading && (
          <div className="p-8 text-center text-slate-500">
            {search || selectedTopics.size > 0 ? "No matching events" : "No events yet"}
          </div>
        )}
      </div>
    </div>
  );
}
