import {
  Radar,
  RadarChart as RechartsRadar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { FeatureValues } from "../../types";

interface Props {
  features: FeatureValues;
  axes: string[];
  colour?: string;
  label?: string;
}

function formatAxisLabel(key: string): string {
  return key
    .replace(/_per90$/, "")
    .replace(/_pct$/, "%")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function RadarChartComponent({ features, axes, colour = "#16a085", label = "Player" }: Props) {
  const data = axes.map((axis) => ({
    label: formatAxisLabel(axis),
    value: features[axis] ?? 0,
    fullName: axis,
  }));

  return (
    <ResponsiveContainer width="100%" height={350}>
      <RechartsRadar data={data} cx="50%" cy="50%" outerRadius="80%">
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis dataKey="label" tick={{ fontSize: 11, fill: "#374151" }} />
        <PolarRadiusAxis tick={false} axisLine={false} />
        <Radar
          name={label}
          dataKey="value"
          stroke={colour}
          fill={colour}
          fillOpacity={0.2}
          strokeWidth={2}
        />
        <Tooltip
          formatter={(value: number) => value.toFixed(2)}
          contentStyle={{ fontSize: 12 }}
        />
      </RechartsRadar>
    </ResponsiveContainer>
  );
}
