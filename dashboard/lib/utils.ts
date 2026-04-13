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
      return "bg-green-100 text-green-700";
    case "offline":
    case "failed":
    case "error":
      return "bg-red-100 text-red-700";
    case "pending":
    case "queued":
      return "bg-yellow-100 text-yellow-700";
    case "running":
    case "in_progress":
      return "bg-blue-100 text-blue-700";
    default:
      return "bg-slate-100 text-slate-600";
  }
}

export function getPriorityColor(priority: string | number): string {
  const p = typeof priority === "number" ? priority : parseInt(String(priority));
  if (p >= 8) return "bg-red-100 text-red-700";
  if (p >= 5) return "bg-orange-100 text-orange-700";
  if (p >= 3) return "bg-yellow-100 text-yellow-700";
  return "bg-slate-100 text-slate-600";
}
