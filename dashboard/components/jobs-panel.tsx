"use client";

import { useState } from "react";
import { api, type Job } from "@/lib/api";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { truncateId, getStatusColor, getPriorityColor, formatRelativeTime } from "@/lib/utils";
import { ChevronDown, ChevronUp, BookOpen, Link2 } from "lucide-react";

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
          className="flex-shrink-0 w-80 bg-slate-50 rounded-lg border"
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
  const [expanded, setExpanded] = useState(false);
  const isActive = !["completed", "failed"].includes(job.status);
  
  // Check if job has context references
  const hasContext = (job.context_job_ids?.length ?? 0) > 0 || job.skill_key;

  const handleClose = async () => {
    if (!window.confirm(`Close job "${job.type}"?`)) return;
    try {
      const res = await api.forceJobStatus(job.job_id, "completed");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    } catch (err: unknown) {
      alert(`Failed to close job: ${err instanceof Error ? err.message : String(err)}`);
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
      
      {(job.depends_on?.length ?? 0) > 0 && (
        <div className="text-xs text-slate-500">
          Depends: {job.depends_on!.map(truncateId).join(", ")}
        </div>
      )}
      
      {/* Context references indicators */}
      {hasContext && (
        <div className="flex items-center gap-2 mt-2">
          {(job.context_job_ids?.length ?? 0) > 0 && (
            <span className="inline-flex items-center gap-1 text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
              <Link2 size={12} />
              {job.context_job_ids?.length} context job{job.context_job_ids?.length !== 1 ? 's' : ''}
            </span>
          )}
          {job.skill_key && (
            <span className="inline-flex items-center gap-1 text-xs text-purple-600 bg-purple-50 px-2 py-0.5 rounded">
              <BookOpen size={12} />
              {job.skill_key}
            </span>
          )}
        </div>
      )}
      
      {/* Expanded context details */}
      {expanded && (
        <div className="mt-3 pt-3 border-t space-y-3">
          {/* Context Jobs */}
          {job.context_jobs && job.context_jobs.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-slate-700 mb-2">Context Jobs</h4>
              <div className="space-y-2">
                {job.context_jobs.map((ctxJob) => (
                  <div key={ctxJob.job_id} className="bg-slate-50 p-2 rounded text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{ctxJob.type}</span>
                      <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                        ctxJob.status === 'completed' ? 'bg-green-100 text-green-800' :
                        ctxJob.status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-slate-100 text-slate-800'
                      }`}>
                        {ctxJob.status}
                      </span>
                    </div>
                    <div className="text-slate-500 mt-1">ID: {truncateId(ctxJob.job_id)}</div>
                    {ctxJob.result && (
                      <pre className="mt-1 text-[10px] bg-slate-100 p-1.5 rounded overflow-x-auto">
                        {JSON.stringify(ctxJob.result, null, 2).slice(0, 200)}
                        {JSON.stringify(ctxJob.result, null, 2).length > 200 && '...'}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Skill */}
          {job.skill && (
            <div>
              <h4 className="text-xs font-medium text-slate-700 mb-2">
                Skill: {job.skill_key}
              </h4>
              <div className="bg-purple-50 p-2 rounded text-xs">
                {'prompt' in job.skill ? (
                  <div>
                    <div className="font-medium text-purple-800 mb-1">Prompt:</div>
                    <div className="text-slate-700 whitespace-pre-wrap">
                      {String(job.skill.prompt).slice(0, 300)}
                      {String(job.skill.prompt).length > 300 && '...'}
                    </div>
                  </div>
                ) : (
                  <pre className="overflow-x-auto">
                    {JSON.stringify(job.skill, null, 2).slice(0, 300)}
                    {JSON.stringify(job.skill, null, 2).length > 300 && '...'}
                  </pre>
                )}
              </div>
            </div>
          )}
          
          {/* Job result if available */}
          {job.result && (
            <div>
              <h4 className="text-xs font-medium text-slate-700 mb-2">Result</h4>
              <pre className="text-xs bg-green-50 p-2 rounded overflow-x-auto">
                {JSON.stringify(job.result, null, 2).slice(0, 400)}
                {JSON.stringify(job.result, null, 2).length > 400 && '...'}
              </pre>
            </div>
          )}
          
          {/* Job error if available */}
          {job.error && (
            <div>
              <h4 className="text-xs font-medium text-red-700 mb-2">Error</h4>
              <div className="text-xs bg-red-50 p-2 rounded text-red-700">
                {job.error.slice(0, 300)}
                {job.error.length > 300 && '...'}
              </div>
            </div>
          )}
        </div>
      )}
      
      <div className="mt-2 pt-2 border-t flex items-center justify-between">
        {hasContext && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700 transition-colors"
          >
            {expanded ? (
              <><ChevronUp size={14} /> Less</>
            ) : (
              <><ChevronDown size={14} /> Details</>
            )}
          </button>
        )}
        {!hasContext && <div />}
        
        {isActive ? (
          <button
            onClick={handleClose}
            className="text-xs text-slate-500 hover:text-slate-700 transition-colors"
          >
            Close
          </button>
        ) : (
          <span className="text-xs text-slate-400">
            {job.created_at ? formatRelativeTime(job.created_at) : ''}
          </span>
        )}
      </div>
    </div>
  );
}
