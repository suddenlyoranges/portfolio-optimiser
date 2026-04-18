import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

const COLORS = [
  "#2c3e6b",
  "#5a7a64",
  "#7c6f5b",
  "#4a6fa5",
  "#8b6e7f",
  "#5d8a6e",
  "#6b7fa3",
  "#a07e5f",
  "#6e8893",
  "#7a6b8a",
];

export default function AllocationPieChart({ weights }) {
  const data = Object.entries(weights || {})
    .filter(([, w]) => w > 0.001)
    .map(([ticker, weight]) => ({
      name: ticker,
      value: +(weight * 100).toFixed(2),
    }))
    .sort((a, b) => b.value - a.value);

  return (
    <ResponsiveContainer width="100%" height={350}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          outerRadius={120}
          dataKey="value"
          label={({ name, value }) => `${name} ${value}%`}
          labelLine={true}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(v) => `${v}%`} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
