"use client";

import { useMemo } from "react";
import { api } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { StatCard } from "@/components/stat-card";
import { AgentsPanel } from "@/components/agents-panel";
import { ActivityFeed } from "@/components/activity-feed";
import { RulesPanel } from "@/components/rules-panel";
import {
  Server,
  Phone,
  ShieldAlert,
  Timer,
} from "lucide-react";

export default function Overview() {

  const { data: services } = useQuery({
    queryKey: ["mcp-services"],
    queryFn: api.listMCPServices,
    refetchInterval: 10000,
  });

  const { data: eventsData } = useQuery({
    queryKey: ["events", "overview"],
    queryFn: () => api.listEvents({ limit: 500 }),
    refetchInterval: 5000,
  });

  const stats = useMemo(() => {
    const events = eventsData?.events ?? [];
    const totalServices = services?.length ?? 0;
    const onlineServices = services?.filter((s) => s.status === "online").length ?? 0;
    const totalCalls = events.length;
    const denials = events.filter((e) => e.status === "error").length;
    const okEvents = events.filter((e) => e.status === "ok" && typeof e.duration_ms === "number");
    const avgResponse = okEvents.length > 0
      ? Math.round(okEvents.reduce((sum, e) => sum + e.duration_ms, 0) / okEvents.length)
      : 0;

    return {
      totalServices,
      onlineServices,
      totalCalls,
      denials,
      avgResponse,
    };
  }, [services, eventsData]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-medium">Overview</h1>
        <p className="text-muted-foreground">Real-time system status</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Services Online"
          value={`${stats.onlineServices} / ${stats.totalServices}`}
          icon={<Server size={20} />}
          trend={stats.onlineServices === stats.totalServices ? "All healthy" : `${stats.totalServices - stats.onlineServices} offline`}
        />
        <StatCard
          title="Calls Today"
          value={stats.totalCalls}
          icon={<Phone size={20} />}
          trend="MCP proxy invocations"
        />
        <StatCard
          title="Denials"
          value={stats.denials}
          icon={<ShieldAlert size={20} />}
          trend={stats.denials > 0 ? "RBAC or timeout errors" : "No errors"}
        />
        <StatCard
          title="Avg Response"
          value={`${stats.avgResponse}ms`}
          icon={<Timer size={20} />}
          trend="Successful calls only"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AgentsPanel />
        <ActivityFeed limit={10} />
      </div>

      <RulesPanel />
    </div>
  );
}
