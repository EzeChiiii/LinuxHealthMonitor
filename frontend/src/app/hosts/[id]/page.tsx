// app/hosts/[id]/page.tsx
// Per-host detail page — shows host info and historical graphs for
// each metric type (CPU, memory, disk). Data fetching stays server-side;
// the actual chart rendering is delegated to a client component.

import { getHost, getHostMetrics } from "@/lib/api";
import MetricChart from "@/components/MetricChart";
import DiagnosticPanel from "@/components/DiagnosticPanel";

function groupByType(metrics: Awaited<ReturnType<typeof getHostMetrics>>) {
  const grouped: Record<string, { time: string; value: number }[]> = {};
  for (const m of metrics) {
    if (!grouped[m.metric_type]) grouped[m.metric_type] = [];
    grouped[m.metric_type].push({
      time: new Date(m.recorded_at).toLocaleTimeString("en-US", { timeZone: "America/New_York" }),
      value: m.value,
    });
  }
  for (const key in grouped) {
    grouped[key].reverse();
  }
  return grouped;
}

export default async function HostDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const hostId = parseInt(id, 10);

  const host = await getHost(hostId);
  const metrics = await getHostMetrics(hostId);
  const grouped = groupByType(metrics);

  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold mb-2">{host.name}</h1>
      <p className="text-sm text-gray-500 mb-6">
        {host.resource_type}
        {host.parent_host_id ? ` — child of host ${host.parent_host_id}` : ""}
      </p>

      <div className="grid gap-8">
        {Object.entries(grouped).map(([metricType, data]) => (
          <div key={metricType}>
            <h2 className="text-lg font-semibold mb-2">{metricType}</h2>
            <MetricChart data={data} />
          </div>
        ))}
      </div>

      <DiagnosticPanel hostId={hostId} />
    </main>
  );
}