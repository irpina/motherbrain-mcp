"use client";

import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: number | string;
  icon?: React.ReactNode;
  trend?: string;
  className?: string;
}

export function StatCard({ title, value, icon, trend, className }: StatCardProps) {
  return (
    <div className={cn("bg-white rounded-lg border p-4 shadow-sm", className)}>
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">{title}</p>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>
      <p className="text-2xl font-bold mt-2">{value}</p>
      {trend && <p className="text-xs text-slate-400 mt-1">{trend}</p>}
    </div>
  );
}
