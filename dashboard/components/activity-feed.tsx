"use client";

import { api } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { formatRelativeTime, truncateId } from "@/lib/utils";

export function ActivityFeed({ limit = 20 }: { limit?: number }) {
  const { data: actions, isLoading } = useQuery({
    queryKey: ["actions", limit],
    queryFn: () => api.listActions(limit),
    refetchInterval: 5000,
  });

  if (isLoading) {
    return <div className="p-4">Loading activity...</div>;
  }

  return (
    <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b bg-slate-50">
        <h2 className="font-semibold">Recent Activity</h2>
      </div>
      <div className="max-h-[400px] overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-600 sticky top-0">
            <tr>
              <th className="px-4 py-2 text-left font-medium">Time</th>
              <th className="px-4 py-2 text-left font-medium">Agent</th>
              <th className="px-4 py-2 text-left font-medium">Action</th>
              <th className="px-4 py-2 text-left font-medium">Job</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {actions?.map((action) => (
              <tr key={action.action_id} className="hover:bg-slate-50">
                <td className="px-4 py-2 text-slate-500">
                  {formatRelativeTime(action.timestamp)}
                </td>
                <td className="px-4 py-2 font-mono">
                  {truncateId(action.agent_id)}
                </td>
                <td className="px-4 py-2">
                  <span className="px-2 py-0.5 bg-slate-100 rounded text-xs">
                    {action.action_type}
                  </span>
                </td>
                <td className="px-4 py-2 font-mono">
                  {action.job_id ? truncateId(action.job_id) : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {actions?.length === 0 && (
          <div className="p-8 text-center text-slate-500">No activity yet</div>
        )}
      </div>
    </div>
  );
}
