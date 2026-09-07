"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChatIcon, LeadsIcon, ScheduleIcon, LogIcon, StatsIcon } from "./icons";

const NAV = [
  { href: "/", label: "对话工作台", icon: ChatIcon },
  { href: "/leads", label: "线索看板", icon: LeadsIcon },
  { href: "/schedules", label: "定时任务", icon: ScheduleIcon },
  { href: "/logs", label: "执行日志", icon: LogIcon },
  { href: "/stats", label: "统计概览", icon: StatsIcon },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-56 shrink-0 h-screen sticky top-0 flex flex-col" style={{ background: "var(--bg-elevated)", borderRight: "1px solid var(--border)" }}>
      <div className="px-5 py-4 flex items-center gap-2 border-b" style={{ borderColor: "var(--border)" }}>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm" style={{ background: "var(--accent)" }}>融</div>
        <div>
          <div className="text-sm font-semibold">融资智能获客</div>
          <div className="text-xs" style={{ color: "var(--text-dim)" }}>AI Agent 工作台</div>
        </div>
      </div>
      <nav className="flex-1 py-3">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link key={href} href={href} className={`flex items-center gap-3 px-5 py-2.5 text-sm transition-colors ${active ? "" : "hover:bg-white/5"}`} style={active ? { background: "rgba(79,140,255,.12)", color: "var(--accent)", borderRight: "3px solid var(--accent)" } : { color: "var(--text-dim)" }}>
              <Icon size={18} />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="px-5 py-3 text-xs border-t" style={{ borderColor: "var(--border)", color: "var(--text-dim)" }}>
        企业融资智能获客系统 v1.0
      </div>
    </aside>
  );
}
