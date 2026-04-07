"use client";

import { api } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { formatRelativeTime } from "@/lib/utils";
import { useState } from "react";

const TOPICS = ["all", "chat", "heartbeat", "proxy", "system"];

const topicColors: Record<string, string> = {
  chat: "bg-blue-100 text-blue-800",
  heartbeat: "bg-green-100 text-green-800",
  proxy: "bg-purple-100 text-purple-800",
  system: "bg-slate-100 text-slate-800",
};

export function ActivityFeed({ limit = 50 }: { limit?: number }) {
  const [topic, setTopic] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["events", limit, topic],
    queryFn: () => api.listEvents({ limit, topic: topic || undefined }),
    refetchInterval: 3000,
  });

  return (
    <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b bg-slate-50 flex items-center gap-2 flex-wrap">
        <h2 className="font-semibold mr-2">Activity Log</h2>
        {TOPICS.map((t) => (
          <button
            key={t}
            onClick={() => setTopic(t === "all" ? "" : t)}
            className={`px-2 py-0.5 rounded text-xs border transition-colors ${
              (t === "all" && !topic) || t === topic
                ? "bg-slate-800 text-white border-slate-800"
                : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
            }`}
          >
            {t}
          </button>
        ))}
        {data && (
          <span className="ml-auto text-xs text-slate-400">{data.count} events</span>
        )}
      </div>
      <div className="max-h-[600px] overflow-y-auto">
        {isLoading && <div className="p-4 text-slate-500">Loading...</div>}
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-600 sticky top-0">
            <tr>
              <th className="px-4 py-2 text-left font-medium">Time</th>
              <th className="px-4 py-2 text-left font-medium">Topic</th>
              <th className="px-4 py-2 text-left font-medium">Service</th>
              <th className="px-4 py-2 text-left font-medium">Tool</th>
              <th className="px-4 py-2 text-left font-medium">Status</th>
              <th className="px-4 py-2 text-left font-medium">ms</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {data?.events.map((event) => (
              <tr key={event.id} className="hover:bg-slate-50">
                <td className="px-4 py-2 text-slate-500 whitespace-nowrap">
                  {formatRelativeTime(event.timestamp)}
                </td>
                <td className="px-4 py-2">
                  <span className={`px-2 py-0.5 rounded text-xs ${topicColors[event.topic] ?? "bg-slate-100 text-slate-700"}`}>
                    {event.topic}
                  </span>
                </td>
                <td className="px-4 py-2 font-mono text-xs text-slate-600">
                  {event.service_id}
                </td>
                <td className="px-4 py-2 font-mono text-xs">
                  {event.tool_name}
                </td>
                <td className="px-4 py-2">
                  <span className={`px-2 py-0.5 rounded text-xs ${event.status === "ok" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
                    {event.status}
                  </span>
                </td>
                <td className="px-4 py-2 text-slate-400 text-xs">
                  {event.duration_ms}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {data?.events.length === 0 && (
          <div className="p-8 text-center text-slate-500">No events yet</div>
        )}
      </div>
    </div>
  );
}
