"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Briefcase, CheckCircle, Clock, User, Loader2 } from "lucide-react";

const categoryBadgeColors: Record<string, string> = {
  frontend: "bg-orange-900/40 text-orange-300 border border-orange-800/50",
  backend: "bg-blue-900/40 text-blue-300 border border-blue-800/50",
  devops: "bg-purple-900/40 text-purple-300 border border-purple-800/50",
  data: "bg-green-900/40 text-green-300 border border-green-800/50",
  qa: "bg-yellow-900/40 text-yellow-300 border border-yellow-800/50",
  research: "bg-pink-900/40 text-pink-300 border border-pink-800/50",
  general: "bg-subtle text-muted-foreground border border-border",
};

const statusIcons: Record<string, React.ReactNode> = {
  open: <Clock size={14} className="text-warning" />,
  claimed: <User size={14} className="text-blue-400" />,
  done: <CheckCircle size={14} className="text-success" />,
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
      console.error("Failed to claim:", err);
    }
  };

  const handleDone = async (jobId: string) => {
    const summary = window.prompt("Enter completion summary:");
    if (!summary) return;
    try {
      await api.completeChatJob(jobId, summary);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    } catch (err: unknown) {
      console.error("Failed to complete:", err);
    }
  };

  return (
    <div className="bg-elevated rounded-lg border border-border overflow-hidden">
      <div className="px-4 py-3 border-b border-border bg-subtle flex items-center justify-between">
        <h2 className="font-medium text-[15px] flex items-center gap-2">
          <Briefcase size={18} strokeWidth={1.5} />
          Jobs
        </h2>
        <div className="flex gap-2">
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="text-xs bg-input border border-border rounded-md px-2 py-1 text-primary focus:outline-none focus:ring-1 focus:ring-accent/50"
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="text-xs bg-input border border-border rounded-md px-2 py-1 text-primary focus:outline-none focus:ring-1 focus:ring-accent/50"
          >
            {statuses.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="divide-y divide-border">
        {isLoading ? (
          <div className="p-8 flex items-center justify-center text-muted-foreground gap-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading jobs...
          </div>
        ) : jobs.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground text-sm">
            <p className="font-medium text-primary mb-1">No jobs found</p>
            <p className="text-xs">Jobs are created from chat messages or via the job board above.</p>
          </div>
        ) : (
          jobs.map((job: any) => (
            <div key={job.id} className="p-4 hover:bg-subtle/50 transition-colors">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs px-2 py-0.5 rounded capitalize ${categoryBadgeColors[job.category] || "bg-subtle text-muted-foreground border border-border"}`}>
                      {job.category}
                    </span>
                    <span className="flex items-center gap-1 text-xs text-muted-foreground">
                      {statusIcons[job.status]}
                      {job.status}
                    </span>
                    {job.claimed_by && (
                      <span className="text-xs text-blue-400">
                        @{job.claimed_by}
                      </span>
                    )}
                  </div>
                  <h3 className="font-medium text-sm text-primary">{job.title}</h3>
                  <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{job.body}</p>
                  {job.summary && (
                    <div className="mt-2 p-2 bg-success-dim text-success text-sm rounded-md border border-success/20">
                      <strong>Summary:</strong> {job.summary}
                    </div>
                  )}
                  <div className="text-xs text-muted-foreground mt-2">
                    #{job.channel} • by {job.created_by}
                  </div>
                </div>
                <div className="flex flex-col gap-1">
                  {job.status === "open" && (
                    <button
                      onClick={() => handleClaim(job.id)}
                      className="px-3 py-1 text-xs bg-accent text-white rounded-md hover:bg-accent-hover transition-colors"
                    >
                      Claim
                    </button>
                  )}
                  {job.status === "claimed" && (
                    <button
                      onClick={() => handleDone(job.id)}
                      className="px-3 py-1 text-xs bg-success text-white rounded-md hover:opacity-90 transition-opacity"
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
