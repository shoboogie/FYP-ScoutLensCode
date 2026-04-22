import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { usePlayerProfile } from "../hooks/usePlayerProfile";
import { useSimilarPlayers } from "../hooks/useSimilarPlayers";
import FilterPanel from "../components/similarity/FilterPanel";
import FeatureWeightSliders from "../components/similarity/FeatureWeightSliders";
import SimilarPlayerCard from "../components/similarity/SimilarPlayerCard";
import RadarChart from "../components/charts/RadarChart";

export default function SimilarityResultsPage() {
  const { id } = useParams<{ id: string }>();
  const playerSeasonId = id ? parseInt(id, 10) : 0;
  const { data: profile } = usePlayerProfile(playerSeasonId);
  const similarity = useSimilarPlayers(playerSeasonId);

  const [customWeights, setCustomWeights] = useState<Record<string, number> | null>(null);

  // Auto-search on page load with defaults
  useEffect(() => {
    if (playerSeasonId) {
      similarity.mutate({ k: 10, role_filter: true });
    }
  }, [playerSeasonId]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleApply = (filters: {
    league: string;
    minMinutes: string;
    roleFilter: boolean;
    k: string;
  }) => {
    similarity.mutate({
      k: parseInt(filters.k) || 10,
      league_filter: filters.league || null,
      min_minutes: parseInt(filters.minMinutes) || 900,
      role_filter: filters.roleFilter,
      feature_weights: customWeights,
    });
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-navy">
          Players Similar to {profile?.player_name ?? "..."}
        </h1>
        {profile && (
          <p className="text-sm text-gray-500">
            {profile.team_name} &middot; {profile.league} &middot;{" "}
            {profile.role_label ?? profile.primary_position}
          </p>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        {/* Sidebar: filters + weight sliders */}
        <div className="space-y-4">
          <FilterPanel onApply={handleApply} isLoading={similarity.isPending} />
          <FeatureWeightSliders onChange={(w) => setCustomWeights(w)} />

          {profile && (
            <div className="rounded-lg bg-white p-4 shadow">
              <h3 className="mb-2 text-sm font-semibold text-navy">Query Player</h3>
              <RadarChart
                features={profile.features}
                axes={profile.radar_axes ?? [
                  "xg_per90", "xa_per90", "progressive_passes_per90",
                  "progressive_carries_per90", "pressures_per90", "aerial_duels_per90",
                ]}
                label={profile.player_name}
              />
            </div>
          )}
        </div>

        {/* Results */}
        <div>
          {similarity.isPending && (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-24 animate-pulse rounded-lg bg-gray-200" />
              ))}
            </div>
          )}

          {similarity.isError && (
            <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
              Search failed. Ensure the backend is running.
            </div>
          )}

          {similarity.data && (
            <>
              <p className="mb-3 text-sm text-gray-500">
                {similarity.data.total} similar player{similarity.data.total !== 1 ? "s" : ""} found
              </p>
              <div className="space-y-3">
                {similarity.data.results.map((player) => (
                  <SimilarPlayerCard
                    key={player.player_id}
                    player={player}
                  />
                ))}
              </div>
              {similarity.data.results.length === 0 && (
                <p className="mt-4 text-center text-sm text-gray-400">
                  No similar players found with current filters. Try relaxing the constraints.
                </p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
