"use client";
// MetricChart.tsx
// A client component wrapping recharts, since charting libraries need
// browser APIs (React context, DOM measurements) that Server Components
// don't have access to. The parent page fetches data on the server and
// passes it in as a prop — only the rendering happens client-side.

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

type DataPoint = { time: string; value: number };

export default function MetricChart({ data }: { data: DataPoint[] }) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="time" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="value" stroke="#8884d8" dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}