import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { RainfallSeries } from "../lib/useStation";

/** Monthly precipitation vs climatology — the signature "draw" motion. */
export default function RainChart({ data }: { data: RainfallSeries }) {
  if (!data.available || !data.months.length) {
    return <div className="muted">No rainfall series available.</div>;
  }
  const rows = data.months.map((m, i) => ({
    month: m.slice(2, 7),
    value: data.values[i],
    clim: data.climatology[i],
  }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={rows} margin={{ top: 8, right: 8, bottom: 4, left: -12 }}>
        <CartesianGrid stroke="rgba(120,200,255,0.08)" strokeDasharray="3 3" />
        <XAxis
          dataKey="month"
          stroke="var(--nn-ink-3)"
          tick={{ fontFamily: "Martian Mono", fontSize: 10 }}
          tickLine={false}
        />
        <YAxis
          stroke="var(--nn-ink-3)"
          tick={{ fontFamily: "Martian Mono", fontSize: 10 }}
          tickLine={false}
          unit=" mm"
        />
        <Tooltip
          contentStyle={{
            background: "var(--nn-raised)",
            border: "1px solid var(--nn-line)",
            borderRadius: 4,
            fontFamily: "Martian Mono",
            fontSize: 11,
            color: "var(--nn-ink)",
          }}
          labelStyle={{ color: "var(--nn-ink-2)" }}
        />
        <Line
          type="monotone"
          dataKey="clim"
          stroke="var(--nn-ink-3)"
          strokeWidth={1}
          strokeDasharray="4 3"
          dot={false}
          name="climatology"
          isAnimationActive={false}
        />
        <Line
          type="monotone"
          dataKey="value"
          stroke="var(--nn-key-glow)"
          strokeWidth={2}
          dot={false}
          name="monthly"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
