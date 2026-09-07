"use client";
import { useState, useEffect } from "react";
import { fetchSchedules, createSchedule, deleteSchedule, type ScheduledJob } from "@/lib/api";
import { TrashIcon } from "@/components/icons";

export default function SchedulesPage() {
  const [jobs, setJobs] = useState<ScheduledJob[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", cron_expr: "0 9 * * 1-5", keyword: "", region: "", count: 20, enabled: true });

  const load = async () => {
    try { setJobs(await fetchSchedules()); } catch {}
  };
  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    try { await createSchedule(form); setForm({ name: "", cron_expr: "0 9 * * 1-5", keyword: "", region: "", count: 20, enabled: true }); setShowForm(false); load(); } catch {}
  };
  const handleDelete = async (id: number) => { await deleteSchedule(id); load(); };

  return (
    <div className="h-screen overflow-y-auto p-6">
      <div className="flex items-center justify-between mb-5">
        <h1 className="text-xl font-semibold">定时任务</h1>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary text-sm px-4 py-2">{showForm ? "取消" : "新建任务"}</button>
      </div>

      {showForm && (
        <div className="card p-5 mb-5 grid grid-cols-2 gap-3">
          <div><label className="text-xs" style={{ color: "var(--text-dim)" }}>任务名称</label><input className="input-dark w-full text-sm mt-1 px-3 py-2" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="如：每日上海专精特新采集" /></div>
          <div><label className="text-xs" style={{ color: "var(--text-dim)" }}>Cron 表达式</label><input className="input-dark w-full text-sm mt-1 px-3 py-2" value={form.cron_expr} onChange={(e) => setForm({ ...form, cron_expr: e.target.value })} /></div>
          <div><label className="text-xs" style={{ color: "var(--text-dim)" }}>关键词</label><input className="input-dark w-full text-sm mt-1 px-3 py-2" value={form.keyword} onChange={(e) => setForm({ ...form, keyword: e.target.value })} /></div>
          <div><label className="text-xs" style={{ color: "var(--text-dim)" }}>地区</label><input className="input-dark w-full text-sm mt-1 px-3 py-2" value={form.region} onChange={(e) => setForm({ ...form, region: e.target.value })} /></div>
          <div><label className="text-xs" style={{ color: "var(--text-dim)" }}>数量</label><input type="number" className="input-dark w-full text-sm mt-1 px-3 py-2" value={form.count} onChange={(e) => setForm({ ...form, count: parseInt(e.target.value) || 20 })} /></div>
          <div className="flex items-end"><button onClick={handleCreate} className="btn-primary text-sm px-4 py-2">创建</button></div>
        </div>
      )}

      {jobs.length === 0 ? (
        <div className="card p-10 text-center text-sm" style={{ color: "var(--text-dim)" }}>暂无定时任务</div>
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <div key={job.id} className="card p-4 flex items-center justify-between">
              <div>
                <div className="font-medium text-sm">{job.name}</div>
                <div className="text-xs mt-1" style={{ color: "var(--text-dim)" }}>
                  Cron: {job.cron_expr} | 关键词: {job.keyword || "—"} | 地区: {job.region || "—"} | 数量: {job.count}
                </div>
                <div className="text-xs mt-0.5" style={{ color: "var(--text-dim)" }}>
                  上次执行: {job.last_run_at ? new Date(job.last_run_at).toLocaleString("zh-CN") : "未执行"}
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`badge ${job.enabled ? "badge-high" : "badge-low"}`}>{job.enabled ? "启用" : "停用"}</span>
                <button onClick={() => handleDelete(job.id)} style={{ color: "#fca5a5" }}><TrashIcon size={16} /></button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
