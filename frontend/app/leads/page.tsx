"use client";
import { useState, useEffect } from "react";
import { fetchLeads, fetchStats, exportLeadsUrl, type Lead, type Stats } from "@/lib/api";
import { TrashIcon } from "@/components/icons";

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [keyword, setKeyword] = useState("");
  const [intention, setIntention] = useState("");
  const [hasPhone, setHasPhone] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const load = async () => {
    setLoading(true);
    try {
      const [data, s] = await Promise.all([
        fetchLeads({ keyword, intention, has_phone: hasPhone, page, page_size: pageSize }),
        fetchStats(),
      ]);
      setLeads(data);
      setStats(s);
      if (page === 1 && !keyword && !intention && !hasPhone) {
        setTotal(s.total_leads);
      }
    } catch {
      setLeads([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [page, intention, hasPhone]);

  return (
    <div className="h-screen overflow-y-auto p-6">
      <div className="flex items-center justify-between mb-5">
        <h1 className="text-xl font-semibold">线索看板</h1>
        <a href={exportLeadsUrl()} className="btn-primary text-sm flex items-center gap-1.5 px-4 py-2">
          导出 CSV
        </a>
      </div>

      {stats && (
        <div className="grid grid-cols-5 gap-3 mb-5">
          {[
            { label: "总线索", value: stats.total_leads, color: "var(--accent)" },
            { label: "高意向", value: stats.high_intention, color: "#fca5a5" },
            { label: "中意向", value: stats.mid_intention, color: "#fcd34d" },
            { label: "低意向", value: stats.low_intention, color: "#d1d5db" },
            { label: "有电话", value: stats.with_phone, color: "var(--green)" },
          ].map((s) => (
            <div key={s.label} className="card p-4 text-center">
              <div className="text-2xl font-bold" style={{ color: s.color }}>{s.value}</div>
              <div className="text-xs mt-1" style={{ color: "var(--text-dim)" }}>{s.label}</div>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-3 mb-4 flex-wrap">
        <input className="input-dark text-sm flex-1 min-w-[200px] px-3 py-2" placeholder="搜索企业名/信用代码" value={keyword} onChange={(e) => setKeyword(e.target.value)} onKeyDown={(e) => e.key === "Enter" && (setPage(1), load())} />
        <select className="input-dark text-sm px-3 py-2" value={intention} onChange={(e) => { setIntention(e.target.value); setPage(1); }}>
          <option value="">全部意向</option>
          <option value="high">高意向</option>
          <option value="mid">中意向</option>
          <option value="low">低意向</option>
        </select>
        <label className="flex items-center gap-2 text-sm cursor-pointer" style={{ color: "var(--text-dim)" }}>
          <input type="checkbox" checked={hasPhone} onChange={(e) => { setHasPhone(e.target.checked); setPage(1); }} />
          仅有电话
        </label>
        <button onClick={() => { setPage(1); load(); }} className="btn-primary text-sm px-4 py-2">搜索</button>
      </div>

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ color: "var(--text-dim)", borderBottom: "1px solid var(--border)" }}>
              <th className="text-left py-3 px-3">企业名称</th>
              <th className="text-left py-3 px-3">法定代表人</th>
              <th className="text-left py-3 px-3">注册资本</th>
              <th className="text-left py-3 px-3">行业</th>
              <th className="text-left py-3 px-3">联系电话</th>
              <th className="text-right py-3 px-3">评分</th>
              <th className="text-center py-3 px-3">意向</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="text-center py-10" style={{ color: "var(--text-dim)" }}>加载中…</td></tr>
            ) : leads.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-10" style={{ color: "var(--text-dim)" }}>暂无线索</td></tr>
            ) : leads.map((l) => (
              <tr key={l.id} style={{ borderBottom: "1px solid var(--border)" }}>
                <td className="py-2.5 px-3">{l.company_name}</td>
                <td className="py-2.5 px-3" style={{ color: "var(--text-dim)" }}>{l.legal_representative || "—"}</td>
                <td className="py-2.5 px-3" style={{ color: "var(--text-dim)" }}>{l.registered_capital || "—"}</td>
                <td className="py-2.5 px-3" style={{ color: "var(--text-dim)" }}>{l.industry || "—"}</td>
                <td className="py-2.5 px-3" style={{ color: l.phone ? "var(--green)" : "var(--text-dim)" }}>{l.phone || "—"}</td>
                <td className="py-2.5 px-3 text-right font-semibold" style={{ color: "var(--accent)" }}>{l.score}</td>
                <td className="py-2.5 px-3 text-center">
                  <span className={`badge badge-${l.intention_level}`}>{l.intention_level === "high" ? "高" : l.intention_level === "mid" ? "中" : "低"}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {!loading && leads.length > 0 && (
        <div className="flex items-center justify-between mt-4 text-sm" style={{ color: "var(--text-dim)" }}>
          <span>第 {page} 页</span>
          <div className="flex gap-2">
            <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1} className="btn-primary px-3 py-1.5 text-xs" style={{ opacity: page === 1 ? 0.4 : 1 }}>上一页</button>
            <button onClick={() => setPage(page + 1)} disabled={leads.length < pageSize} className="btn-primary px-3 py-1.5 text-xs" style={{ opacity: leads.length < pageSize ? 0.4 : 1 }}>下一页</button>
          </div>
        </div>
      )}
    </div>
  );
}
