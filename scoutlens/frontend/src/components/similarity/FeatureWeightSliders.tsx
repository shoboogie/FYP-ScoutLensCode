import { useState } from "react";

const DIMENSIONS = [
  { key: "ATK", label: "Attacking" },
  { key: "CRE", label: "Creativity" },
  { key: "PAS", label: "Passing" },
  { key: "CAR", label: "Carrying" },
  { key: "DEF", label: "Defending" },
  { key: "AER", label: "Physicality" },
];

interface Props {
  onChange: (weights: Record<string, number>) => void;
}

export default function FeatureWeightSliders({ onChange }: Props) {
  const [weights, setWeights] = useState<Record<string, number>>(() =>
    Object.fromEntries(DIMENSIONS.map((d) => [d.key, 1.0]))
  );

  const handleSlider = (key: string, value: number) => {
    const updated = { ...weights, [key]: value };
    setWeights(updated);
    onChange(updated);
  };

  const reset = () => {
    const defaults = Object.fromEntries(DIMENSIONS.map((d) => [d.key, 1.0]));
    setWeights(defaults);
    onChange(defaults);
  };

  return (
    <div className="rounded-lg bg-white p-4 shadow">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-navy">Dimension Weights</h3>
        <button onClick={reset} className="text-xs text-teal hover:underline">
          Reset
        </button>
      </div>

      <div className="space-y-3">
        {DIMENSIONS.map(({ key, label }) => (
          <div key={key}>
            <div className="flex justify-between text-xs text-gray-600">
              <span>{label}</span>
              <span className="tabular-nums">{weights[key].toFixed(1)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={weights[key]}
              onChange={(e) => handleSlider(key, parseFloat(e.target.value))}
              className="w-full accent-teal"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
