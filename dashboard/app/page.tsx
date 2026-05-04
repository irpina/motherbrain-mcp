"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { StatCard } from "@/components/stat-card";
import { AgentsPanel } from "@/components/agents-panel";
import { ActivityFeed } from "@/components/activity-feed";
import { RulesPanel } from "@/components/rules-panel";
import { CreateJobDialog } from "@/components/create-job-dialog";
import {
  Users,
  Briefcase,
  Clock,
  CheckCircle,
  Plus,
} from "lucide-react";

export default function Overview() {
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const { data: agents } = useQuery({
    queryKey: ["agents"],
    queryFn: api.listAgents,
    refetchInterval: 5000,
  });

  const { data: jobs } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => api.listJobs(),
    refetchInterval: 5000,
  });

  const stats = {
    totalAgents: agents?.length ?? 0,
    onlineAgents:
      agents?.filter((a) => a.status === "online").length ?? 0,
    pendingJobs: jobs?.filter((j) => j.status === "pending").length ?? 0,
    runningJobs: jobs?.filter((j) => j.status === "running").length ?? 0,
    completedJobs: jobs?.filter((j) => j.status === "completed").length ?? 0,
    failedJobs: jobs?.filter((j) => j.status === "failed").length ?? 0,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Overview</h1>
          <p className="text-slate-500">Real-time system status</p>
        </div>
        <button
          onClick={() => setIsCreateOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-md hover:bg-slate-800"
        >
          <Plus size={18} />
          New Job
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Agents"
          value={stats.totalAgents}
          icon={<Users size={20} />}
          trend={`${stats.onlineAgents} online`}
        />
        <StatCard
          title="Pending Jobs"
          value={stats.pendingJobs}
          icon={<Clock size={20} />}
          trend="Waiting for agents"
        />
        <StatCard
          title="Running Jobs"
          value={stats.runningJobs}
          icon={<Briefcase size={20} />}
          trend="In progress"
        />
        <StatCard
          title="Completed"
          value={stats.completedJobs}
          icon={<CheckCircle size={20} />}
          trend={`${stats.failedJobs} failed`}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AgentsPanel />
        <ActivityFeed limit={10} />
      </div>

      <RulesPanel />

      <CreateJobDialog isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} />
    </div>
  );
}
