"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Users,
  Briefcase,
  Database,
  Activity,
  Server,
  Shield,
  UserCog,
  MessageSquare,
  ScrollText,
  Settings,
} from "lucide-react";

const navItems = [
  { href: "/", label: "Overview", icon: LayoutDashboard },
  { href: "/mcp", label: "MCP Services", icon: Server },
  { href: "/activity", label: "Activity", icon: Activity },
  { href: "/agents", label: "Agents", icon: Users },
  { href: "/jobs", label: "Jobs", icon: Briefcase },
  { href: "/context", label: "Context", icon: Database },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/rules", label: "Rules", icon: ScrollText },
];

const adminItems = [
  { href: "/admin/users", label: "Users", icon: UserCog },
  { href: "/admin/groups", label: "Groups", icon: Shield },
  { href: "/admin/settings", label: "Settings", icon: Settings },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <nav className="w-64 bg-[#0c0c14] text-[var(--text-primary)] min-h-screen p-4 flex flex-col border-r border-[var(--border-subtle)]">
      <div className="mb-8 px-2">
        <h1 className="text-xl font-medium flex items-center gap-2.5 tracking-tight">
          <span className="w-2.5 h-2.5 bg-accent rounded-full animate-pulse shadow-[0_0_8px_var(--accent)]" />
          Motherbrain
        </h1>
        <p className="text-xs text-muted-foreground mt-1.5 px-5">MCP Dashboard</p>
      </div>
      <ul className="space-y-0.5">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                  isActive
                    ? "bg-subtle text-primary border-l-[3px] border-l-accent"
                    : "text-muted-foreground hover:text-primary hover:bg-subtle/60"
                )}
              >
                <Icon size={18} strokeWidth={1.5} />
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
      <div className="mt-8">
        <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider px-3 mb-2">
          Admin
        </h2>
        <ul className="space-y-0.5">
          {adminItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                    isActive
                      ? "bg-subtle text-primary border-l-[3px] border-l-accent"
                      : "text-muted-foreground hover:text-primary hover:bg-subtle/60"
                  )}
                >
                  <Icon size={18} strokeWidth={1.5} />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}
