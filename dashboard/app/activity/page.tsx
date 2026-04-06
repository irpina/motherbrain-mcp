"use client";

import { ActivityFeed } from "@/components/activity-feed";

export default function ActivityPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Activity Log</h1>
        <p className="text-slate-500">Full audit trail of all agent actions</p>
      </div>
      <ActivityFeed limit={100} />
    </div>
  );
}
