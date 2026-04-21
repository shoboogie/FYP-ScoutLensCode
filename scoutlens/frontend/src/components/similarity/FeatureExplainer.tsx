import type { FeatureContribution } from "../../types";

interface Props {
  contributions: FeatureContribution[];
  overallSimilarity: number;
  dimensionSimilarities: Record<string, number>;
}

function formatFeatureName(key: string): string {
  return key
    .replace(/_per90$/, " /90")
    .replace(/_pct$/, " %")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function FeatureExplainer({
  contributions,
  overallSimilarity,
  dimensionSimilarities,
}: Props) {
  const matchPct = Math.round(overallSimilarity * 100);

  return (
    <div className="rounded-lg bg-white p-4 shadow">
      <h3 className="mb-3 text-sm font-semibold text-navy">
        Similarity Breakdown &mdash; {matchPct}% overall match
      </h3>

      {/* Dimension-level summary */}
      <div className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-3">
        {Object.entries(dimensionSimilarities).map(([dim, score]) => {
          const pct = Math.round(score * 100);
          return (
            <div key={dim} className="rounded bg-gray-50 p-2 text-center">
              <p className="text-xs text-gray-500">{dim}</p>
              <p className="text-lg font-bold text-navy">{pct}%</p>
            </div>
          );
        })}
      </div>

      {/* Top feature contributions */}
      <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
        Top Contributing Features
      </h4>
      <div className="space-y-1.5">
        {contributions.slice(0, 10).map((c) => {
          const isPositive = c.contribution > 0;
          return (
            <div key={c.feature} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <span
                  className={`inline-block h-2 w-2 rounded-full ${
                    isPositive ? "bg-emerald-500" : "bg-red-400"
                  }`}
                />
                <span className="text-gray-700">{formatFeatureName(c.feature)}</span>
                <span className="text-xs text-gray-400">{c.dimension}</span>
              </div>
              <span className={`tabular-nums ${isPositive ? "text-emerald-600" : "text-red-500"}`}>
                {isPositive ? "+" : ""}{(c.contribution * 100).toFixed(1)}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
