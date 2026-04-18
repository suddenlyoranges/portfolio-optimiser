import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

export default function BacktestLineChart({ data }) {
  const chartData = (data || []).map((d) => ({
    date: d.date,
    value: d.value,
  }));

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart
        data={chartData}
        margin={{ top: 20, right: 30, bottom: 20, left: 20 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11 }}
          tickFormatter={(d) => d.slice(5)}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fontSize: 12 }}
          tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`}
          label={{
            value: "Portfolio Value ($)",
            angle: -90,
            position: "insideLeft",
          }}
        />
        <Tooltip
          formatter={(v) => [`$${Number(v).toLocaleString()}`, "Value"]}
          labelFormatter={(l) => `Date: ${l}`}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="value"
          name="Portfolio Value"
          stroke="#2c3e6b"
          dot={false}
          strokeWidth={2}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
