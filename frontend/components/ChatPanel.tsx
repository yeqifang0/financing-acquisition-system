"use client";
import { useState, useRef, useCallback } from "react";
import { chatStreamUrl, type Lead } from "@/lib/api";
import { SendIcon, CheckIcon, SpinnerIcon } from "./icons";

interface Step {
  index: number;
  key: string;
  name: string;
  desc: string;
  status: "pending" | "running" | "done" | "error";
  result?: string;
  error?: string;
}

interface Summary {
  total: number;
  high: number;
  mid: number;
  low: number;
  with_phone: number;
  top10: Array<{
    company_name: string;
    phone: string;
    industry: string;
    registered_capital: string;
    score: number;
    intention_level: string;
  }>;
}

interface Msg {
  role: "user" | "assistant";
  text?: string;
  params?: Record<string, any>;
  steps?: Step[];
  logs?: string[];
  summary?: Summary;
  error?: string;
  loading?: boolean;
}

const SUGGESTIONS = [
  "我要找上海的专精特新企业，要电话",
  "搜索北京半导体高新技术企业50条",
  "采集深圳新能源企业线索30条",
];

export default function ChatPanel() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
    }, 50);
  }, []);

  const sendMessage = async (text: string) => {
    if (!text.trim() || busy) return;
    setInput("");
    setBusy(true);
    const userMsg: Msg = { role: "user", text };
    const assistantMsg: Msg = { role: "assistant", loading: true, logs: [] };
    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    scrollToBottom();

    try {
      const res = await fetch(chatStreamUrl(), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const reader = res.body?.getReader();
      if (!reader) return;
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let eventType = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            const data = JSON.parse(line.slice(6));
            handleEvent(eventType, data, assistantMsg);
          }
        }
        setMessages((prev) => {
          const next = [...prev];
          next[next.length - 1] = { ...assistantMsg, loading: false };
          return next;
        });
        scrollToBottom();
      }
    } catch (e: any) {
      assistantMsg.error = `请求失败: ${e.message}`;
      setMessages((prev) => {
        const next = [...prev];
        next[next.length - 1] = { ...assistantMsg, loading: false, error: assistantMsg.error };
        return next;
      });
    } finally {
      setBusy(false);
    }
  };

  const handleEvent = (type: string, data: any, msg: Msg) => {
    switch (type) {
      case "text":
        msg.text = (msg.text || "") + (msg.text ? "\n" : "") + data.text;
        break;
      case "params":
        msg.params = data;
        break;
      case "steps":
        msg.steps = data.steps;
        break;
      case "step":
        if (msg.steps) {
          const idx = data.index - 1;
          if (msg.steps[idx]) {
            msg.steps[idx] = { ...msg.steps[idx], status: data.status, result: data.result, error: data.error };
          }
        }
        break;
      case "log":
        msg.logs = [...(msg.logs || []), data.text];
        break;
      case "card":
        msg.summary = data.summary;
        break;
      case "error":
        msg.error = data.message;
        break;
      case "done":
        msg.summary = data.summary;
        break;
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center" style={{ color: "var(--text-dim)" }}>
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4 text-2xl font-bold" style={{ background: "var(--bg-elevated)", color: "var(--accent)" }}>AI</div>
            <h2 className="text-lg font-semibold mb-1" style={{ color: "var(--text)" }}>企业融资智能获客</h2>
            <p className="text-sm">输入采集指令，AI 自动执行 6 步获客流水线</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-3xl ${msg.role === "user" ? "text-right" : "w-full"}`}>
              {msg.role === "user" ? (
                <div className="inline-block px-4 py-2.5 rounded-2xl text-sm" style={{ background: "var(--accent)", color: "#fff" }}>{msg.text}</div>
              ) : (
                <div className="space-y-3">
                  {msg.loading && !msg.text && !msg.steps && (
                    <div className="flex items-center gap-2 text-sm" style={{ color: "var(--text-dim)" }}>
                      <SpinnerIcon /> Agent 执行中…
                    </div>
                  )}
                  {msg.text && <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</div>}
                  {msg.error && <div className="text-sm px-3 py-2 rounded-lg" style={{ background: "rgba(239,68,68,.1)", color: "#fca5a5" }}>{msg.error}</div>}
                  {msg.params && (
                    <div className="card p-4 text-sm">
                      <div className="font-semibold mb-2" style={{ color: "var(--accent)" }}>采集参数</div>
                      <div className="grid grid-cols-2 gap-2" style={{ color: "var(--text-dim)" }}>
                        <div>关键词: <span style={{ color: "var(--text)" }}>{msg.params.keyword}</span></div>
                        <div>地区: <span style={{ color: "var(--text)" }}>{msg.params.region || "不限"}</span></div>
                        <div>数量: <span style={{ color: "var(--text)" }}>{msg.params.count}</span></div>
                        <div>数据源: <span style={{ color: "var(--text)" }}>{msg.params.data_source}</span></div>
                      </div>
                    </div>
                  )}
                  {msg.steps && (
                    <div className="card p-4">
                      <div className="font-semibold mb-3 text-sm" style={{ color: "var(--accent)" }}>执行流水线</div>
                      <div className="space-y-2">
                        {msg.steps.map((step) => (
                          <div key={step.index} className="flex items-center gap-3 text-sm">
                            <div className="w-5 h-5 rounded-full flex items-center justify-center shrink-0" style={{
                              background: step.status === "done" ? "var(--green)" : step.status === "error" ? "var(--red)" : step.status === "running" ? "var(--accent)" : "var(--border)",
                              color: "#fff",
                            }}>
                              {step.status === "done" ? <CheckIcon size={12} /> : step.status === "running" ? <SpinnerIcon size={12} /> : step.status === "error" ? "!" : <span className="text-xs">{step.index}</span>}
                            </div>
                            <span style={{ color: step.status === "pending" ? "var(--text-dim)" : "var(--text)" }}>{step.name}</span>
                            {step.result && <span className="text-xs" style={{ color: "var(--text-dim)" }}>{step.result}</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {msg.logs && msg.logs.length > 0 && (
                    <div className="card p-3 text-xs font-mono space-y-1" style={{ background: "var(--bg)", maxHeight: "180px", overflowY: "auto" }}>
                      {msg.logs.map((log, j) => (
                        <div key={j} style={{ color: "var(--text-dim)" }}>{log}</div>
                      ))}
                    </div>
                  )}
                  {msg.summary && (
                    <div className="space-y-3">
                      <div className="card p-4">
                        <div className="font-semibold mb-3 text-sm" style={{ color: "var(--accent)" }}>执行总结</div>
                        <div className="grid grid-cols-5 gap-3 text-center">
                          <div><div className="text-2xl font-bold">{msg.summary.total}</div><div className="text-xs" style={{ color: "var(--text-dim)" }}>总线索</div></div>
                          <div><div className="text-2xl font-bold" style={{ color: "#fca5a5" }}>{msg.summary.high}</div><div className="text-xs" style={{ color: "var(--text-dim)" }}>高意向</div></div>
                          <div><div className="text-2xl font-bold" style={{ color: "#fcd34d" }}>{msg.summary.mid}</div><div className="text-xs" style={{ color: "var(--text-dim)" }}>中意向</div></div>
                          <div><div className="text-2xl font-bold" style={{ color: "#d1d5db" }}>{msg.summary.low}</div><div className="text-xs" style={{ color: "var(--text-dim)" }}>低意向</div></div>
                          <div><div className="text-2xl font-bold" style={{ color: "var(--green)" }}>{msg.summary.with_phone}</div><div className="text-xs" style={{ color: "var(--text-dim)" }}>有电话</div></div>
                        </div>
                      </div>
                      {msg.summary.top10 && msg.summary.top10.length > 0 && (
                        <div className="card p-4 overflow-x-auto">
                          <div className="font-semibold mb-3 text-sm" style={{ color: "var(--accent)" }}>Top 10 推荐名单</div>
                          <table className="w-full text-sm">
                            <thead>
                              <tr style={{ color: "var(--text-dim)", borderBottom: "1px solid var(--border)" }}>
                                <th className="text-left py-2 px-2">企业名称</th>
                                <th className="text-left py-2 px-2">联系电话</th>
                                <th className="text-left py-2 px-2">行业</th>
                                <th className="text-right py-2 px-2">评分</th>
                                <th className="text-center py-2 px-2">意向</th>
                              </tr>
                            </thead>
                            <tbody>
                              {msg.summary.top10.map((t, j) => (
                                <tr key={j} style={{ borderBottom: "1px solid var(--border)" }}>
                                  <td className="py-2 px-2">{t.company_name}</td>
                                  <td className="py-2 px-2" style={{ color: "var(--text-dim)" }}>{t.phone || "—"}</td>
                                  <td className="py-2 px-2" style={{ color: "var(--text-dim)" }}>{t.industry || "—"}</td>
                                  <td className="py-2 px-2 text-right font-semibold" style={{ color: "var(--accent)" }}>{t.score}</td>
                                  <td className="py-2 px-2 text-center">
                                    <span className={`badge badge-${t.intention_level}`}>{t.intention_level === "high" ? "高" : t.intention_level === "mid" ? "中" : "低"}</span>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      <div className="border-t px-6 py-4" style={{ borderColor: "var(--border)" }}>
        {messages.length === 0 && (
          <div className="flex gap-2 mb-3 flex-wrap">
            {SUGGESTIONS.map((s) => (
              <button key={s} onClick={() => sendMessage(s)} className="px-3 py-1.5 rounded-full text-xs border transition-colors hover:bg-white/5" style={{ borderColor: "var(--border)", color: "var(--text-dim)" }}>
                {s}
              </button>
            ))}
          </div>
        )}
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage(input)}
            placeholder="输入获客指令，如：找上海专精特新企业30条"
            className="flex-1 input-dark px-4 py-2.5 text-sm"
            disabled={busy}
          />
          <button onClick={() => sendMessage(input)} disabled={busy} className="btn-primary flex items-center gap-1.5 px-5 py-2.5 text-sm">
            <SendIcon size={16} /> 发送
          </button>
        </div>
      </div>
    </div>
  );
}
