const BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

export interface Lead {
  id: number;
  company_name: string;
  credit_code: string | null;
  legal_representative: string | null;
  registered_capital: string | null;
  registered_address: string | null;
  business_scope: string | null;
  establish_date: string | null;
  enterprise_status: string | null;
  industry: string | null;
  phone: string | null;
  email: string | null;
  website: string | null;
  is_small_micro: boolean | null;
  enterprise_scale: string | null;
  insurance_count: number | null;
  is_listed: boolean | null;
  score: number;
  intention_level: string;
  score_dimensions: Record<string, any> | null;
  data_source: string | null;
  created_at: string | null;
}

export interface Stats {
  total_leads: number;
  high_intention: number;
  mid_intention: number;
  low_intention: number;
  with_phone: number;
  avg_score: number;
}

export interface ScheduledJob {
  id: number;
  name: string;
  cron_expr: string;
  keyword: string;
  region: string;
  count: number;
  enabled: boolean;
  last_run_at: string | null;
  created_at: string | null;
}

export interface CrawlTask {
  id: number;
  keyword: string;
  region: string | null;
  status: string;
  total: number;
  processed: number;
  error: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string | null;
}

export interface ScoringDimension {
  key: string;
  name: string;
  weight: number;
}

export async function fetchLeads(params: {
  keyword?: string;
  intention?: string;
  min_score?: number;
  has_phone?: boolean;
  page?: number;
  page_size?: number;
} = {}): Promise<Lead[]> {
  const sp = new URLSearchParams();
  if (params.keyword) sp.set("keyword", params.keyword);
  if (params.intention) sp.set("intention", params.intention);
  if (params.min_score) sp.set("min_score", String(params.min_score));
  if (params.has_phone) sp.set("has_phone", "true");
  sp.set("page", String(params.page || 1));
  sp.set("page_size", String(params.page_size || 20));
  const res = await fetch(`${BASE}/leads?${sp}`);
  if (!res.ok) throw new Error("fetch leads failed");
  return res.json();
}

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${BASE}/leads/stats`);
  if (!res.ok) throw new Error("fetch stats failed");
  return res.json();
}

export async function fetchConfig(): Promise<{
  data_source: string;
  has_credentials: boolean;
  use_mock: boolean;
  scoring_dimensions: ScoringDimension[];
}> {
  const res = await fetch(`${BASE}/config`);
  if (!res.ok) throw new Error("fetch config failed");
  return res.json();
}

export async function fetchSchedules(): Promise<ScheduledJob[]> {
  const res = await fetch(`${BASE}/schedules`);
  if (!res.ok) throw new Error("fetch schedules failed");
  return res.json();
}

export async function createSchedule(job: Omit<ScheduledJob, "id" | "last_run_at" | "created_at">): Promise<ScheduledJob> {
  const res = await fetch(`${BASE}/schedules`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(job),
  });
  if (!res.ok) throw new Error("create schedule failed");
  return res.json();
}

export async function deleteSchedule(id: number): Promise<void> {
  await fetch(`${BASE}/schedules/${id}`, { method: "DELETE" });
}

export async function fetchTasks(page = 1): Promise<CrawlTask[]> {
  const res = await fetch(`${BASE}/tasks?page=${page}`);
  if (!res.ok) throw new Error("fetch tasks failed");
  return res.json();
}

export function chatStreamUrl(): string {
  return `${BASE}/chat/stream`;
}

export function exportLeadsUrl(): string {
  return `${BASE}/leads/export`;
}
