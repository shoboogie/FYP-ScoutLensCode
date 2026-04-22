import { useState } from "react";

interface Filters {
  league: string;
  minMinutes: string;
  roleFilter: boolean;
  k: string;
}

interface Props {
  onApply: (filters: Filters) => void;
  isLoading: boolean;
}

const LEAGUES = ["", "Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1"];

export default function FilterPanel({ onApply, isLoading }: Props) {
  const [filters, setFilters] = useState<Filters>({
    league: "",
    minMinutes: "900",
    roleFilter: true,
    k: "10",
  });

  const update = (key: keyof Filters, value: string | boolean) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="rounded-lg bg-white p-4 shadow">
      <h3 className="mb-3 text-sm font-semibold text-navy">Filters</h3>

      <div className="space-y-3 text-sm">
        <div>
          <label className="mb-1 block text-gray-600">League</label>
          <select
            value={filters.league}
            onChange={(e) => update("league", e.target.value)}
            className="w-full rounded border border-gray-300 px-2 py-1.5"
          >
            {LEAGUES.map((l) => (
              <option key={l} value={l}>{l || "All leagues"}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-gray-600">Min. minutes</label>
          <input
            type="number"
            value={filters.minMinutes}
            onChange={(e) => update("minMinutes", e.target.value)}
            className="w-full rounded border border-gray-300 px-2 py-1.5"
          />
        </div>

        <div>
          <label className="mb-1 block text-gray-600">Results</label>
          <input
            type="number"
            value={filters.k}
            onChange={(e) => update("k", e.target.value)}
            min="1"
            max="50"
            className="w-full rounded border border-gray-300 px-2 py-1.5"
          />
        </div>

        <label className="flex items-center gap-2 text-gray-700">
          <input
            type="checkbox"
            checked={filters.roleFilter}
            onChange={(e) => update("roleFilter", e.target.checked)}
            className="rounded"
          />
          Same role only
        </label>

        <button
          onClick={() => onApply(filters)}
          disabled={isLoading}
          className="w-full rounded bg-teal py-2 text-white font-medium hover:bg-teal-dark disabled:opacity-50 transition-colors"
        >
          {isLoading ? "Searching..." : "Find Similar Players"}
        </button>
      </div>
    </div>
  );
}
