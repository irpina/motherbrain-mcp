"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Briefcase, CheckCircle, Clock, User } from "lucide-react";

const categoryColors: Record<string, string> = {
  frontend: "bg-orange-100 text-orange-800",
  backend: "bg-blue-100 text-blue-800",
  devops: "bg-purple-100 text-purple-800",
  data: "bg-green-100 text-green-800",
  qa: "bg-yellow-100 text-yellow-800",
  research: "bg-pink-100 text-pink-800",
  general: "bg-slate-100 text-slate-800",
};

const statusIcons: Record<string, React.ReactNode> = {
  open: <Clock size={14} className="text-yellow-600" />,
  claimed: <User size={14} className="text-blue-600" />,
  done: <CheckCircle size={14} className="text-green-600" />,
};

export function JobsPanel() {
  const queryClient = useQueryClient();
  const [filterCategory, setFilterCategory] = useState("");
  const [filterStatus, setFilterStatus] = useState("open");

  const { data: jobsData, isLoading } = useQuery({
    queryKey: ["jobs", filterCategory, filterStatus],
    queryFn: () => api.listChatJobs({ category: filterCategory || undefined, status: filterStatus, limit: 50 }),
    refetchInterval: 10000,
  });

  const jobs = jobsData?.jobs || [];

  const categories = ["frontend", "backend", "devops", "data", "qa", "research", "general"];
  const statuses = ["open", "claimed", "done"];

  const handleClaim = async (jobId: string) => {
    try {
      await api.claimChatJob(jobId);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    } catch (err: unknown) {
      alert(`Failed to claim: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const handleDone = async (jobId: string) => {
    const summary = window.prompt("Enter completion summary:");
    if (!summary) return;
    try {
      await api.completeChatJob(jobId, summary);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    } catch (err: unknown) {
      alert(`Failed to complete: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  return (
    <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b bg-slate-50 flex items-center justify-between">
        <h2 className="font-semibold flex items-center gap-2">
          <Briefcase size={18} />
          Jobs
        </h2>
        <div className="flex gap-2">
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="text-xs border rounded px-2 py-1"
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="text-xs border rounded px-2 py-1"
          >
            {statuses.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="divide-y">
        {isLoading ? (
          <div className="p-4 text-sm text-slate-400">Loading jobs...</div>
        ) : jobs.length === 0 ? (
          <div className="p-8 text-center text-slate-500">No jobs found</div>
        ) : (
          jobs.map((job: any) => (
            <div key={job.id} className="p-4 hover:bg-slate-50">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs px-2 py-0.5 rounded capitalize ${categoryColors[job.category] || "bg-slate-100"}`}>
                      {job.category}
                    </span>
                    <span className="flex items-center gap-1 text-xs text-slate-500">
                      {statusIcons[job.status]}
                      {job.status}
                    </span>
                    {job.claimed_by && (
                      <span className="text-xs text-blue-600">
                        @{job.claimed_by}
                      </span>
                    )}
                  </div>
                  <h3 className="font-medium text-sm">{job.title}</h3>
                  <p className="text-sm text-slate-600 mt-1 line-clamp-2">{job.body}</p>
                  {job.summary && (
                    <div className="mt-2 p-2 bg-green-50 text-green-800 text-sm rounded">
                      <strong>Summary:</strong> {job.summary}
                    </div>
                  )}
                  <div className="text-xs text-slate-400 mt-2">
                    #{job.channel} • by {job.created_by}
                  </div>
                </div>
                <div className="flex flex-col gap-1">
                  {job.status === "open" && (
                    <button
                      onClick={() => handleClaim(job.id)}
                      className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Claim
                    </button>
                  )}
                  {job.status === "claimed" && (
                    <button
                      onClick={() => handleDone(job.id)}
                      className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
                    >
                      Done
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
