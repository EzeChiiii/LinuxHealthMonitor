// app/alerts/page.tsx
// Shows the full history of alert events — both active and resolved —
// most recent first.

import { getAlertEvents } from "@/lib/api";

export default async function AlertsPage() {
  const events = await getAlertEvents();

  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold mb-6">Alert history</h1>

      <div className="grid gap-3">
        {events.length === 0 && (
          <p className="text-gray-500">No alerts recorded yet.</p>
        )}

        {events.map((event) => (
          <div
            key={event.id}
            className={`border rounded-lg p-4 flex justify-between items-center ${
              event.status === "active" ? "border-red-400 bg-red-50" : "border-gray-200"
            }`}
          >
            <div>
              <p className="font-semibold">
                {event.status === "active" ? "🔴 Active" : "✅ Resolved"} — rule #{event.alert_rule_id}
              </p>
              <p className="text-sm text-gray-500">
                Triggered value: {event.triggered_value}
              </p>
            </div>
            <div className="text-sm text-gray-500 text-right">
              <p>Triggered: {new Date(event.triggered_at).toLocaleString("en-US", { timeZone: "America/New_York" })}</p>
              {event.resolved_at && (
                <p>Resolved: {new Date(event.resolved_at).toLocaleString("en-US", { timeZone: "America/New_York" })}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}