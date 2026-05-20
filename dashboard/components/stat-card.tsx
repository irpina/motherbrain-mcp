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
    <div className={cn("bg-elevated rounded-lg border border-border p-5", className)}>
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{title}</p>
        {icon && (
          <div className="bg-accent-dim text-accent p-2 rounded-md">
            {icon}
          </div>
        )}
      </div>
      <p className="text-3xl font-medium text-primary mt-3">{value}</p>
      {trend && <p className="text-xs text-muted-foreground mt-1.5">{trend}</p>}
    </div>
  );
}
