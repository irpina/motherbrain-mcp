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
  { href: "/agents", label: "Agents", icon: Users },
  { href: "/jobs", label: "Jobs", icon: Briefcase },
  { href: "/mcp", label: "MCP Services", icon: Server },
  { href: "/context", label: "Context", icon: Database },
  { href: "/activity", label: "Activity", icon: Activity },
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
    <nav className="w-64 bg-slate-900 text-slate-100 min-h-screen p-4">
      <div className="mb-8">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          Motherbrain
        </h1>
        <p className="text-xs text-slate-400 mt-1">MCP Dashboard</p>
      </div>
      <ul className="space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                  isActive
                    ? "bg-slate-800 text-white"
                    : "text-slate-400 hover:text-white hover:bg-slate-800"
                )}
              >
                <Icon size={18} />
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
      <div className="mt-8">
        <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-3 mb-2">
          Admin
        </h2>
        <ul className="space-y-1">
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
                      ? "bg-slate-800 text-white"
                      : "text-slate-400 hover:text-white hover:bg-slate-800"
                  )}
                >
                  <Icon size={18} />
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
