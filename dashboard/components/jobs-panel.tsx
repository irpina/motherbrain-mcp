"use client";

import { api, type Job } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { truncateId, getStatusColor, getPriorityColor } from "@/lib/utils";

const statuses = ["pending", "assigned", "running", "completed", "failed"];

export function JobsPanel() {
  const { data: jobs, isLoading } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => api.listJobs(),
    refetchInterval: 5000,
  });

  if (isLoading) {
    return <div className="p-4">Loading jobs...</div>;
  }

  const jobsByStatus = statuses.reduce((acc, status) => {
    acc[status] = jobs?.filter((j) => j.status === status) || [];
    return acc;
  }, {} as Record<string, Job[]>);

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {statuses.map((status) => (
        <div
          key={status}
          className="flex-shrink-0 w-72 bg-slate-50 rounded-lg border"
        >
          <div className="px-3 py-2 border-b bg-slate-100 rounded-t-lg">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${getStatusColor(status)}`} />
              <span className="font-semibold capitalize">{status}</span>
              <span className="ml-auto text-xs text-slate-500 bg-white px-2 py-0.5 rounded-full">
                {jobsByStatus[status].length}
              </span>
            </div>
          </div>
          <div className="p-2 space-y-2 min-h-[100px]">
            {jobsByStatus[status].map((job) => (
              <JobCard key={job.job_id} job={job} />
            ))}
            {jobsByStatus[status].length === 0 && (
              <div className="text-center text-slate-400 text-sm py-4">
                No jobs
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function JobCard({ job }: { job: Job }) {
  const queryClient = useQueryClient();
  const isActive = !["completed", "failed"].includes(job.status);

  const handleClose = async () => {
    if (!window.confirm(`Close job "${job.type}"?`)) return;
    try {
      const res = await api.forceJobStatus(job.job_id, "completed");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    } catch (err) {
      alert(`Failed to close job: ${err}`);
    }
  };

  return (
    <div className="bg-white p-3 rounded-md border shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <div className="font-medium text-sm truncate">{job.type}</div>
        <span
          className={`text-xs px-2 py-0.5 rounded border ${getPriorityColor(
            job.priority
          )}`}
        >
          {job.priority}
        </span>
      </div>
      <div className="text-xs text-slate-500 mt-1">
        ID: {truncateId(job.job_id)}
      </div>
      {job.assigned_agent && (
        <div className="text-xs text-slate-500">
          Agent: {truncateId(job.assigned_agent)}
        </div>
      )}
      {job.depends_on.length > 0 && (
        <div className="text-xs text-slate-500">
          Depends: {job.depends_on.map(truncateId).join(", ")}
        </div>
      )}
      {isActive && (
        <div className="mt-2 pt-2 border-t">
          <button
            onClick={handleClose}
            className="text-xs text-slate-500 hover:text-slate-700 transition-colors"
          >
            Close
          </button>
        </div>
      )}
    </div>
  );
}
