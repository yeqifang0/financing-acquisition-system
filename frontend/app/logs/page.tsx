"use client";
import { useState, useEffect } from "react";
import { fetchTasks, type CrawlTask } from "@/lib/api";

export default function LogsPage() {
  const [tasks, setTasks] = useState<CrawlTask[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTasks()
      .then(setTasks)
      .catch(() => setTasks([]))
      .finally(() => setLoading(false));
  }, []);

  const statusColor = (s: string) => {
    if (s === "completed") return "#fcd34d";
    if (s === "running") return "var(--accent)";
    if (s === "failed") return "#fca5a5";
    return "var(--text-dim)";
  };

  return (
    <div className="h-screen overflow-y-auto p-6">
      <h1 className="text-xl font-semibold mb-5">执行日志</h1>
      {loading ? (
        <div className="text-center py-10 text-sm" style={{ color: "var(--text-dim)" }}>加载中…</div>
      ) : tasks.length === 0 ? (
        <div className="card p-10 text-center text-sm" style={{ color: "var(--text-dim)" }}>暂无执行记录</div>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ color: "var(--text-dim)", borderBottom: "1px solid var(--border)" }}>
                <th className="text-left py-3 px-3">ID</th>
                <th className="text-left py-3 px-3">关键词</th>
                <th className="text-left py-3 px-3">地区</th>
                <th className="text-center py-3 px-3">状态</th>
                <th className="text-center py-3 px-3">总数</th>
                <th className="text-center py-3 px-3">已处理</th>
                <th className="text-left py-3 px-3">创建时间</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((t) => (
                <tr key={t.id} style={{ borderBottom: "1px solid var(--border)" }}>
                  <td className="py-2.5 px-3">{t.id}</td>
                  <td className="py-2.5 px-3">{t.keyword}</td>
                  <td className="py-2.5 px-3" style={{ color: "var(--text-dim)" }}>{t.region || "—"}</td>
                  <td className="py-2.5 px-3 text-center">
                    <span className="badge" style={{ background: `rgba(${statusColor(t.status) === "var(--accent)" ? "79,140,255" : statusColor(t.status) === "#fca5a5" ? "239,68,68" : statusColor(t.status) === "#fcd34d" ? "245,158,11" : "156,163,175"},.15)`, color: statusColor(t.status) }}>
                      {t.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-center">{t.total}</td>
                  <td className="py-2.5 px-3 text-center">{t.processed}</td>
                  <td className="py-2.5 px-3" style={{ color: "var(--text-dim)" }}>{t.created_at ? new Date(t.created_at).toLocaleString("zh-CN") : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
