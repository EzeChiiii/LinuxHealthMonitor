// app/page.tsx
// The main dashboard page — shows all monitored hosts with their
// current status. Uses a Server Component (default in the App Router)
// so the data fetch happens on the server, not in the browser.

import { getHosts } from "@/lib/api";
import Link from "next/link";

export default async function DashboardPage() {
  const hosts = await getHosts();

  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold mb-6">Sentinel — Host overview</h1>
      
      <a href="/alerts" className="text-blue-600 underline text-sm mb-6 inline-block">
        View alert history →
      </a>

      <div className="grid gap-4">
        {hosts.map((host) => (
          <Link key={host.id} href={`/hosts/${host.id}`}>
            <div className="border rounded-lg p-4 flex justify-between items-center hover:bg-gray-50 cursor-pointer">
              <div>
                <p className="font-semibold">{host.name}</p>
                <p className="text-sm text-gray-500">
                  {host.resource_type}
                  {host.parent_host_id ? ` — child of host ${host.parent_host_id}` : ""}
                </p>
              </div>
              <div className="text-sm text-gray-500">
                {host.last_seen_at
                  ? `Last seen: ${new Date(host.last_seen_at).toLocaleTimeString("en-US", { timeZone: "America/New_York" })}`
                  : "Never reported"}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </main>
  );
}