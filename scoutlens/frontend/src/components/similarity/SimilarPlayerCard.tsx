import { Link } from "react-router-dom";
import type { SimilarPlayerResult } from "../../types";
import PlayerBadge from "../player/PlayerBadge";

interface Props {
  player: SimilarPlayerResult;
}

export default function SimilarPlayerCard({ player }: Props) {
  const matchPct = Math.round(player.similarity_score * 100);

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

      <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-gray-600">
        <span>{player.minutes_played} min</span>
        {player.role_label && <PlayerBadge role={player.role_label} />}
      </div>
    </div>
  );
}
