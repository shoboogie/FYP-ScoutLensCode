import { useState } from "react";
import { usePlayerSearch } from "../hooks/usePlayerSearch";
import PlayerCard from "../components/player/PlayerCard";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [league, setLeague] = useState("");

  const { data, isLoading, isError } = usePlayerSearch({ q: query, league: league || undefined });

  return (
    <div>
      <div className="mb-6">
        <h1 className="mb-2 text-2xl font-bold text-navy">Player Search</h1>
        <p className="text-sm text-gray-500">
          Search across 1,500+ players from Europe&apos;s Big Five leagues (2015/16)
        </p>
      </div>

      <div className="mb-6 flex gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by player name..."
          className="flex-1 rounded-lg border border-gray-300 px-4 py-2.5 text-sm shadow-sm focus:border-teal focus:outline-none focus:ring-1 focus:ring-teal"
        />
        <select
          value={league}
          onChange={(e) => setLeague(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2.5 text-sm shadow-sm"
        >
          <option value="">All leagues</option>
          <option value="Premier League">Premier League</option>
          <option value="La Liga">La Liga</option>
          <option value="Bundesliga">Bundesliga</option>
          <option value="Serie A">Serie A</option>
          <option value="Ligue 1">Ligue 1</option>
        </select>
      </div>

      {query.length > 0 && query.length < 2 && (
        <p className="text-sm text-gray-400">Type at least 2 characters to search</p>
      )}

      {isLoading && (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 animate-pulse rounded-lg bg-gray-200" />
          ))}
        </div>
      )}

      {isError && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700">
          Failed to load results. Check the backend is running on port 8000.
        </div>
      )}

      {data && (
        <>
          <p className="mb-3 text-sm text-gray-500">
            {data.total} player{data.total !== 1 ? "s" : ""} found
          </p>
          <div className="space-y-3">
            {data.results.map((player) => (
              <PlayerCard key={player.player_season_id} player={player} />
            ))}
          </div>
          {data.results.length === 0 && query.length >= 2 && (
            <p className="mt-4 text-center text-sm text-gray-400">
              No players match &ldquo;{query}&rdquo;
            </p>
          )}
        </>
      )}
    </div>
  );
}
