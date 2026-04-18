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

export default function EfficientFrontierChart({ frontier, optimal }) {
  const frontierData = (frontier || []).map((p) => ({
    volatility: +(p.volatility * 100).toFixed(2),
    return: +(p.expected_return * 100).toFixed(2),
  }));

  const specialPoints = [];
  if (optimal) {
    specialPoints.push({
      volatility: +(optimal.volatility * 100).toFixed(2),
      return: +(optimal.expected_return * 100).toFixed(2),
    });
  }

  return (
    <ResponsiveContainer width="100%" height={440}>
      <ScatterChart margin={{ top: 20, right: 30, bottom: 60, left: 70 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="volatility"
          name="Volatility"
          unit="%"
          type="number"
          label={{
            value: "Volatility (%)",
            position: "bottom",
            offset: 0,
          }}
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
            offset: -20,
            style: { textAnchor: "middle" },
          }}
          tick={{ fontSize: 12 }}
        />
        <Tooltip
          formatter={(value, name) => [
            `${value}%`,
            name === "return" ? "Return" : "Volatility",
          ]}
        />
        <Legend wrapperStyle={{ paddingTop: 20 }} />
        <Scatter
          name="Efficient Frontier"
          data={frontierData}
          fill="#2c3e6b"
          opacity={0.6}
          r={3}
        />
        {specialPoints.length > 0 && (
          <Scatter
            name="Optimal Portfolio"
            data={specialPoints}
            fill="#dc2626"
            r={8}
            shape="star"
          />
        )}
      </ScatterChart>
    </ResponsiveContainer>
  );
}
