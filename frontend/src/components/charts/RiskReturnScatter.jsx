import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

const COLORS = ["#6366f1", "#ef4444", "#10b981", "#f59e0b", "#ec4899"];

export default function RiskReturnScatter({ portfolios }) {
  return (
    <ResponsiveContainer width="100%" height={420}>
      <ScatterChart margin={{ top: 20, right: 30, bottom: 40, left: 20 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="volatility"
          name="Volatility"
          unit="%"
          type="number"
          label={{ value: "Volatility (%)", position: "bottom", offset: 0 }}
          tick={{ fontSize: 12 }}
        />
        <YAxis
          dataKey="return"
          name="Return"
          unit="%"
          type="number"
          label={{
            value: "Expected Return (%)",
            angle: -90,
            position: "insideLeft",
            offset: 0,
          }}
          tick={{ fontSize: 12 }}
        />
        <Tooltip
          formatter={(value, name) => [
            `${value}%`,
            name === "volatility" ? "Volatility" : "Return",
          ]}
          cursor={{ strokeDasharray: "3 3" }}
        />
        <Legend
          verticalAlign="top"
          align="right"
          wrapperStyle={{ paddingBottom: 8 }}
        />
        {(portfolios || []).map((p, i) => (
          <Scatter
            key={p.name}
            name={p.name}
            data={[
              {
                volatility: +(p.volatility * 100).toFixed(2),
                return: +(p.expectedReturn * 100).toFixed(2),
              },
            ]}
            fill={COLORS[i % COLORS.length]}
            r={10}
          />
        ))}
      </ScatterChart>
    </ResponsiveContainer>
  );
}
