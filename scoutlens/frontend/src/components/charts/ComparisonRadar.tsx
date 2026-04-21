import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import type { FeatureValues } from "../../types";

interface Props {
  queryFeatures: FeatureValues;
  targetFeatures: FeatureValues;
  axes: string[];
  queryName: string;
  targetName: string;
}

function formatAxisLabel(key: string): string {
  return key
    .replace(/_per90$/, "")
    .replace(/_pct$/, "%")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function ComparisonRadar({
  queryFeatures,
  targetFeatures,
  axes,
  queryName,
  targetName,
}: Props) {
  const data = axes.map((axis) => ({
    label: formatAxisLabel(axis),
    [queryName]: queryFeatures[axis] ?? 0,
    [targetName]: targetFeatures[axis] ?? 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={400}>
      <RadarChart data={data} cx="50%" cy="50%" outerRadius="80%">
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis dataKey="label" tick={{ fontSize: 11, fill: "#374151" }} />
        <PolarRadiusAxis tick={false} axisLine={false} />
        <Radar
          name={queryName}
          dataKey={queryName}
          stroke="#16a085"
          fill="#16a085"
          fillOpacity={0.15}
          strokeWidth={2}
        />
        <Radar
          name={targetName}
          dataKey={targetName}
          stroke="#e74c3c"
          fill="#e74c3c"
          fillOpacity={0.1}
          strokeWidth={2}
        />
        <Legend />
        <Tooltip
          formatter={(value: number) => value.toFixed(2)}
          contentStyle={{ fontSize: 12 }}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
