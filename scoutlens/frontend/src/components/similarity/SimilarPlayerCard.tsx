import { useState } from "react";
import { Link } from "react-router-dom";
import type { SimilarPlayerResult } from "../../types";
import PlayerBadge from "../player/PlayerBadge";
import { useAddToShortlist } from "../../hooks/useShortlist";
import { useAuth } from "../../hooks/useAuth";

interface Props {
  player: SimilarPlayerResult;
}

export default function SimilarPlayerCard({ player }: Props) {
  const matchPct = Math.round(player.similarity_score * 100);
  const { isAuthenticated } = useAuth();
  const addToShortlist = useAddToShortlist();
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    addToShortlist.mutate(
      { player_season_id: player.player_season_id, notes: "" },
      {
        onSuccess: () => setSaved(true),
        onError: () => setSaved(true),
      },
    );
  };

  return (
    <div className="rounded-lg bg-white p-4 shadow">
      <div className="flex items-start justify-between">
        <div>
          <Link
            to={`/player/${player.player_season_id}`}
            className="text-lg font-semibold text-navy hover:text-teal transition-colors"
          >
            {player.player_name}
          </Link>
          <p className="text-sm text-gray-500">
            {player.team_name} &middot; {player.league}
          </p>
        </div>

        <div className="text-right">
          <span className="text-2xl font-bold text-teal">{matchPct}%</span>
          <p className="text-xs text-gray-400">match</p>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between">
        <div className="flex items-center gap-3 text-xs text-gray-600">
          <span>{player.minutes_played} min</span>
          {player.role_label && <PlayerBadge role={player.role_label} />}
        </div>

        {isAuthenticated && (
          <button
            onClick={handleSave}
            disabled={saved || addToShortlist.isPending}
            className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
              saved
                ? "bg-gray-200 text-gray-500"
                : "bg-navy text-white hover:bg-navy-light"
            }`}
          >
            {saved ? "Saved" : "Save"}
          </button>
        )}
      </div>
    </div>
  );
}
