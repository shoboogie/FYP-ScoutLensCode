import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { usePlayerProfile } from "../hooks/usePlayerProfile";
import { useAddToShortlist } from "../hooks/useShortlist";
import { useAuth } from "../hooks/useAuth";
import PlayerBadge from "../components/player/PlayerBadge";
import PlayerStatsTable from "../components/player/PlayerStatsTable";
import RadarChart from "../components/charts/RadarChart";

export default function PlayerProfilePage() {
  const { id } = useParams<{ id: string }>();
  const playerSeasonId = id ? parseInt(id, 10) : undefined;
  const { data: profile, isLoading, isError } = usePlayerProfile(playerSeasonId);
  const { isAuthenticated } = useAuth();
  const addToShortlist = useAddToShortlist();
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    if (!playerSeasonId) return;
    addToShortlist.mutate(
      { player_season_id: playerSeasonId, notes: "" },
      {
        onSuccess: () => setSaved(true),
        onError: () => setSaved(true), // already on shortlist
      },
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-gray-200" />
        <div className="h-64 animate-pulse rounded-lg bg-gray-200" />
      </div>
    );
  }

  if (isError || !profile) {
    return (
      <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
        Player not found. <Link to="/" className="underline">Back to search</Link>
      </div>
    );
  }

  const radarAxes = profile.radar_axes ?? [
    "xg_per90", "xa_per90", "progressive_passes_per90",
    "progressive_carries_per90", "pressures_per90", "aerial_duels_per90",
  ];

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-navy">{profile.player_name}</h1>
            <p className="text-gray-500">
              {profile.team_name} &middot; {profile.league} &middot; {profile.season}
            </p>
          </div>
          <div className="flex gap-2">
            {isAuthenticated && (
              <button
                onClick={handleSave}
                disabled={saved || addToShortlist.isPending}
                className={`rounded px-4 py-2 text-sm font-medium transition-colors ${
                  saved
                    ? "bg-gray-300 text-gray-600 cursor-default"
                    : "bg-navy text-white hover:bg-navy-light"
                }`}
              >
                {saved ? "Saved to Shortlist" : addToShortlist.isPending ? "Saving..." : "Save to Shortlist"}
              </button>
            )}
            <Link
              to={`/similar/${profile.player_season_id}`}
              className="rounded bg-teal px-4 py-2 text-sm font-medium text-white hover:bg-teal-dark transition-colors"
            >
              Find Similar Players
            </Link>
          </div>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-gray-600">
          <span>{profile.minutes_played} minutes</span>
          <span>{profile.matches_played} matches</span>
          {profile.primary_position && (
            <span className="rounded bg-gray-100 px-2 py-0.5">{profile.primary_position}</span>
          )}
          {profile.role_label && <PlayerBadge role={profile.role_label} />}
          {profile.role_confidence !== null && (
            <span className="text-xs text-gray-400">
              {Math.round(profile.role_confidence * 100)}% confidence
            </span>
          )}
        </div>

        {profile.role_summary && (
          <p className="mt-3 rounded-lg bg-navy/5 p-3 text-sm italic text-gray-700">
            {profile.role_summary}
          </p>
        )}
      </div>

      {/* Radar + Stats */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg bg-white p-4 shadow">
          <h2 className="mb-2 text-sm font-semibold text-navy">
            {profile.role_label ? `${profile.role_label} Radar` : "Player Radar"}
          </h2>
          <RadarChart
            features={profile.features}
            axes={radarAxes}
            label={profile.player_name}
          />
        </div>

        <div className="rounded-lg bg-white p-4 shadow">
          <h2 className="mb-3 text-sm font-semibold text-navy">Dimension Scores</h2>
          <div className="space-y-2">
            {profile.dimension_scores.map((ds) => (
              <div key={ds.dimension}>
                <div className="flex justify-between text-xs text-gray-600">
                  <span>{ds.dimension}</span>
                  <span className="tabular-nums">{ds.percentile.toFixed(2)}</span>
                </div>
                <div className="h-2 rounded-full bg-gray-200">
                  <div
                    className="h-2 rounded-full bg-teal transition-all"
                    style={{ width: `${Math.min(ds.percentile * 10, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Full stats table */}
      <div className="mt-6">
        <h2 className="mb-3 text-sm font-semibold text-navy">Per-90 Statistics</h2>
        <PlayerStatsTable
          features={profile.features}
          highlightFeatures={radarAxes}
        />
      </div>
    </div>
  );
}
