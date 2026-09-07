"use client";
import { useState, useEffect } from "react";
import { fetchStats, fetchConfig, type Stats, type ScoringDimension } from "@/lib/api";

const DIMENSION_DETAILS = [
  { key: "scale", name: "企业规模", weight: "15%", rule: "大型95 | 中型80 | 小型65 | 微型45" },
  { key: "industry", name: "行业属性", weight: "15%", rule: "半导体/新能源/生物医药92 | 机械/软件78 | 其他55" },
  { key: "qualification", name: "资质认证", weight: "20%", rule: "专精特新/小巨人96 | 高新技术88 | 科技72 | 普通50" },
  { key: "capital", name: "注册资本", weight: "10%", rule: ">1亿92 | 5000万+82 | 1000万+72 | <1000万50" },
  { key: "years", name: "经营年限", weight: "10%", rule: ">10年92 | 5-10年80 | 2-5年70 | <2年55" },
  { key: "status", name: "企业状态", weight: "10%", rule: "存续/在营92 | 迁出40 | 注销/吊销10" },
  { key: "insurance", name: "参保人数", weight: "10%", rule: ">500人92 | 100+82 | 50+72 | <50人50" },
  { key: "listing", name: "上市信息", weight: "10%", rule: "已上市92 | 未上市60" },
];

export default function StatsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [dims, setDims] = useState<ScoringDimension[]>([]);

  useEffect(() => {
    fetchStats().then(setStats).catch(() => {});
    fetchConfig().then((c) => setDims(c.scoring_dimensions)).catch(() => {});
  }, []);

  const cards = stats ? [
    { label: "线索总数", value: stats.total_leads, color: "var(--accent)" },
    { label: "高意向", value: stats.high_intention, color: "#fca5a5" },
    { label: "中意向", value: stats.mid_intention, color: "#fcd34d" },
    { label: "低意向", value: stats.low_intention, color: "#d1d5db" },
    { label: "有电话", value: stats.with_phone, color: "var(--green)" },
    { label: "平均分", value: stats.avg_score, color: "var(--accent)" },
  ] : [];

  return (
    <div className="h-screen overflow-y-auto p-6">
      <h1 className="text-xl font-semibold mb-5">统计概览</h1>

      <div className="grid grid-cols-6 gap-3 mb-6">
        {cards.length === 0 ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="card p-4 h-20" style={{ background: "var(--bg)" }} />
          ))
        ) : cards.map((c) => (
          <div key={c.label} className="card p-4 text-center">
            <div className="text-2xl font-bold" style={{ color: c.color }}>{c.value}</div>
            <div className="text-xs mt-1" style={{ color: "var(--text-dim)" }}>{c.label}</div>
          </div>
        ))}
      </div>

      <div className="card p-5">
        <h2 className="font-semibold mb-4 text-sm" style={{ color: "var(--accent)" }}>8 维度融资意向评分模型</h2>
        <table className="w-full text-sm">
          <thead>
            <tr style={{ color: "var(--text-dim)", borderBottom: "1px solid var(--border)" }}>
              <th className="text-left py-3 px-3">维度</th>
              <th className="text-center py-3 px-3">权重</th>
              <th className="text-left py-3 px-3">评分规则</th>
            </tr>
          </thead>
          <tbody>
            {DIMENSION_DETAILS.map((d) => (
              <tr key={d.key} style={{ borderBottom: "1px solid var(--border)" }}>
                <td className="py-2.5 px-3 font-medium">{d.name}</td>
                <td className="py-2.5 px-3 text-center">
                  <span className="badge badge-mid">{d.weight}</span>
                </td>
                <td className="py-2.5 px-3" style={{ color: "var(--text-dim)" }}>{d.rule}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="mt-4 text-xs" style={{ color: "var(--text-dim)" }}>
          意向分级：高意向 ≥ 80 分 | 中意向 60–79 分 | 低意向 &lt; 60 分
        </div>
      </div>
    </div>
  );
}
