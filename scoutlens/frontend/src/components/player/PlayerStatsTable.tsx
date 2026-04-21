import type { FeatureValues } from "../../types";

interface Props {
  features: FeatureValues;
  highlightFeatures?: string[];
}

// Group features by dimension for display
const DIMENSIONS: { name: string; features: string[] }[] = [
  {
    name: "Attacking",
    features: [
      "xg_per90", "shots_per90", "shots_on_target_per90", "goals_per90",
      "npxg_per90", "touches_in_box_per90", "xg_per_shot",
    ],
  },
  {
    name: "Chance Creation",
    features: [
      "xa_per90", "key_passes_per90", "assists_per90", "passes_into_box_per90",
      "through_balls_per90", "progressive_passes_per90", "crosses_per90",
    ],
  },
  {
    name: "Passing",
    features: [
      "passes_attempted_per90", "pass_completion_pct", "progressive_pass_distance_per90",
      "long_passes_per90", "long_pass_completion_pct", "switches_per90",
      "passes_under_pressure_pct",
    ],
  },
  {
    name: "Carrying",
    features: [
      "progressive_carries_per90", "carry_distance_per90", "progressive_carry_distance_per90",
      "carries_into_box_per90", "dribbles_attempted_per90", "dribble_success_pct",
      "ball_receipts_per90",
    ],
  },
  {
    name: "Defending",
    features: [
      "pressures_per90", "pressure_success_pct", "tackles_per90", "tackle_success_pct",
      "interceptions_per90", "blocks_per90", "ball_recoveries_per90", "clearances_per90",
    ],
  },
  {
    name: "Aerial / Physical",
    features: [
      "aerial_duels_per90", "aerial_win_pct", "ground_duels_per90",
      "ground_duel_win_pct", "fouls_won_per90", "dispossessed_per90",
    ],
  },
];

function formatFeatureName(key: string): string {
  return key
    .replace(/_per90$/, " /90")
    .replace(/_pct$/, " %")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function PlayerStatsTable({ features, highlightFeatures = [] }: Props) {
  return (
    <div className="space-y-4">
      {DIMENSIONS.map((dim) => (
        <div key={dim.name}>
          <h4 className="mb-2 text-sm font-semibold text-navy">{dim.name}</h4>
          <div className="overflow-hidden rounded-lg border border-gray-200">
            <table className="w-full text-sm">
              <tbody>
                {dim.features.map((feat, i) => {
                  const value = features[feat] ?? 0;
                  const isHighlighted = highlightFeatures.includes(feat);
                  return (
                    <tr
                      key={feat}
                      className={`${i % 2 === 0 ? "bg-white" : "bg-gray-50"} ${
                        isHighlighted ? "font-semibold text-teal-dark" : ""
                      }`}
                    >
                      <td className="px-3 py-1.5 text-gray-700">{formatFeatureName(feat)}</td>
                      <td className="px-3 py-1.5 text-right tabular-nums">
                        {typeof value === "number" ? value.toFixed(2) : value}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  );
}
