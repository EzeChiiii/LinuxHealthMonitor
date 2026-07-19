"use client";
// DiagnosticPanel.tsx
// Lets the user trigger an on-demand diagnostic (ping, DNS lookup, etc.)
// against a target, then polls the API every 2 seconds until the agent
// has finished running it and reported a result back.

import { useState } from "react";
import { triggerDiagnostic, getDiagnosticRun, DiagnosticRun } from "@/lib/api";

const DIAGNOSTIC_TYPES = ["ping", "traceroute", "dns_lookup", "port_check", "http_check"];

export default function DiagnosticPanel({ hostId }: { hostId: number }) {
  const [diagnosticType, setDiagnosticType] = useState("ping");
  const [target, setTarget] = useState("8.8.8.8");
  const [run, setRun] = useState<DiagnosticRun | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setRun(null);

    const triggered = await triggerDiagnostic(hostId, diagnosticType, target);
    setRun(triggered);

    // Poll every 2 seconds until status is no longer "pending".
    // Poll every 2 seconds until status is no longer "pending".
    const interval = setInterval(async () => {
      try {
        const updated = await getDiagnosticRun(triggered.id);
        setRun(updated);
        if (updated.status !== "pending") {
          clearInterval(interval);
          setLoading(false);
        }
      } catch (err) {
        // Stop polling on error instead of retrying forever — e.g. if
        // the API becomes unreachable mid-poll.
        console.error("Polling failed:", err);
        clearInterval(interval);
        setLoading(false);
      }
    }, 2000);
  }

  return (
    <div className="border rounded-lg p-4 mt-8">
      <h2 className="text-lg font-semibold mb-4">Run a diagnostic</h2>

      <form onSubmit={handleSubmit} className="flex gap-2 mb-4">
        <select
          value={diagnosticType}
          onChange={(e) => setDiagnosticType(e.target.value)}
          className="border rounded px-2 py-1"
        >
          {DIAGNOSTIC_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
        <input
          type="text"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          placeholder="target (e.g. 8.8.8.8 or host:port)"
          className="border rounded px-2 py-1 flex-1"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-black text-white rounded px-4 py-1 disabled:opacity-50"
        >
          {loading ? "Running..." : "Run"}
        </button>
      </form>

      {run && (
        <div className="bg-white text-black border rounded p-3 text-sm">
          <p>
            Status: <span className="font-medium">{run.status}</span>
          </p>
          {run.result && (
            <pre className="mt-2 whitespace-pre-wrap text-xs bg-gray-100 text-black p-2 rounded">
              {JSON.stringify(run.result, null, 2)}
            </pre>
          )}
        </div>
      )}
      
    </div>
  );
}