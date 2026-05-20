import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function truncateId(id: string, length = 8): string {
  if (!id) return "";
  return id.length > length ? id.slice(0, length) + "…" : id;
}

export function formatRelativeTime(timestamp: string | number | Date): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  if (diffSecs < 60) return diffSecs <= 1 ? "just now" : `${diffSecs}s ago`;
  const diffMins = Math.floor(diffSecs / 60);
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export function getStatusColor(status: string): string {
  switch (status?.toLowerCase()) {
    case "online":
    case "completed":
    case "active":
    case "ok":
      return "bg-success";
    case "offline":
    case "failed":
    case "error":
      return "bg-danger";
    case "pending":
    case "queued":
      return "bg-warning";
    case "running":
    case "in_progress":
      return "bg-blue-500";
    default:
      return "bg-muted-foreground/30";
  }
}

export function getStatusBadgeColor(status: string): string {
  switch (status?.toLowerCase()) {
    case "online":
    case "completed":
    case "active":
    case "ok":
      return "bg-success-dim text-success border border-success/20";
    case "offline":
    case "failed":
    case "error":
      return "bg-destructive-dim text-destructive border border-destructive/20";
    case "pending":
    case "queued":
      return "bg-warning-dim text-warning border border-warning/20";
    case "running":
    case "in_progress":
      return "bg-blue-900/40 text-blue-300 border border-blue-800/50";
    default:
      return "bg-subtle text-muted-foreground border border-border";
  }
}

export function getTopicBadgeColor(topic: string): string {
  switch (topic?.toLowerCase()) {
    case "chat":
      return "bg-blue-900/40 text-blue-300 border border-blue-800/50";
    case "heartbeat":
      return "bg-green-900/40 text-green-300 border border-green-800/50";
    case "proxy":
      return "bg-purple-900/40 text-purple-300 border border-purple-800/50";
    case "system":
      return "bg-subtle text-muted-foreground border border-border";
    default:
      return "bg-subtle text-muted-foreground border border-border";
  }
}

export function getProtocolBadgeColor(protocol: string): string {
  switch (protocol?.toLowerCase()) {
    case "mcp":
      return "bg-blue-900/40 text-blue-300 border border-blue-800/50";
    case "rest":
      return "bg-purple-900/40 text-purple-300 border border-purple-800/50";
    default:
      return "bg-subtle text-muted-foreground border border-border";
  }
}

export function getPriorityColor(priority: string | number): string {
  const p = typeof priority === "number" ? priority : parseInt(String(priority));
  if (p >= 8) return "bg-destructive-dim text-destructive border border-destructive/20";
  if (p >= 5) return "bg-orange-900/40 text-orange-300 border border-orange-800/50";
  if (p >= 3) return "bg-warning-dim text-warning border border-warning/20";
  return "bg-subtle text-muted-foreground border border-border";
}
