"use client";

import { useState } from "react";
import { JobsPanel } from "@/components/jobs-panel";
import { CreateJobDialog } from "@/components/create-job-dialog";
import { Plus } from "lucide-react";

export default function JobsPage() {
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Jobs</h1>
          <p className="text-slate-500">Job board and queue status</p>
        </div>
        <button
          onClick={() => setIsCreateOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-md hover:bg-slate-800"
        >
          <Plus size={18} />
          New Job
        </button>
      </div>
      <JobsPanel />
      <CreateJobDialog isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} />
    </div>
  );
}
