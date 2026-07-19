// lib/api.ts
// Centralizes all calls to the Sentinel API in one place, so every
// component uses the same base URL and auth header instead of
// repeating fetch() boilerplate everywhere.

const API_URL =
  typeof window === "undefined"
    ? process.env.API_URL_INTERNAL || "http://localhost:8000"  // server-side
    : process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"; // browser

const TOKEN = process.env.NEXT_PUBLIC_AGENT_TOKEN;

const headers = {
  "Content-Type": "application/json",
  "X-Agent-Token": TOKEN as string,
};

// Matches the shape returned by GET /hosts/{name} and POST /hosts
export type Host = {
  id: number;
  name: string;
  resource_type: string;
  parent_host_id: number | null;
  last_seen_at: string | null;
  created_at: string;
};


export async function getHosts(): Promise<Host[]> {
  const res = await fetch(`${API_URL}/hosts`, { headers, cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch hosts: ${res.status}`);
  return res.json();
}

// Matches the shape returned by GET /hosts/{host_id}/metrics
export type Metric = {
  id: number;
  host_id: number;
  metric_type: string;
  value: number;
  recorded_at: string;
};

// Matches the shape returned by POST /diagnostics and GET /diagnostics/{id}
export type DiagnosticRun = {
  id: number;
  host_id: number;
  diagnostic_type: string;
  target: string;
  status: string;
  result: Record<string, unknown> | null;
  requested_at: string;
  completed_at: string | null;
};

// Matches the shape returned by GET /alert-events
export type AlertEvent = {
  id: number;
  alert_rule_id: number;
  triggered_value: number;
  status: string;
  triggered_at: string;
  resolved_at: string | null;
};

export async function getAlertEvents(): Promise<AlertEvent[]> {
  const res = await fetch(`${API_URL}/alert-events`, { headers, cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch alert events: ${res.status}`);
  return res.json();
}


export async function triggerDiagnostic(
  hostId: number,
  diagnosticType: string,
  target: string
): Promise<DiagnosticRun> {
  const res = await fetch(`${API_URL}/diagnostics`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      host_id: hostId,
      diagnostic_type: diagnosticType,
      target,
    }),
  });
  if (!res.ok) throw new Error(`Failed to trigger diagnostic: ${res.status}`);
  return res.json();
}

export async function getDiagnosticRun(id: number): Promise<DiagnosticRun> {
  const res = await fetch(`${API_URL}/diagnostics/${id}`, { headers, cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch diagnostic run: ${res.status}`);
  return res.json();
}


export async function getHost(hostId: number): Promise<Host> {
  const res = await fetch(`${API_URL}/hosts/by-id/${hostId}`, { headers, cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch host: ${res.status}`);
  return res.json();
}

export async function getHostMetrics(hostId: number): Promise<Metric[]> {
  const res = await fetch(`${API_URL}/hosts/${hostId}/metrics`, { headers, cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to fetch metrics: ${res.status}`);
  return res.json();
}

