import { Link } from "react-router-dom";
import type { PlayerCard as PlayerCardType } from "../../types";
import PlayerBadge from "./PlayerBadge";

interface Props {
  player: PlayerCardType;
}

export default function PlayerCard({ player }: Props) {
  return (
    <Link
      to={`/player/${player.player_season_id}`}
      className="block rounded-lg bg-white p-4 shadow hover:shadow-md transition-shadow"
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-navy">{player.player_name}</h3>
          <p className="text-sm text-gray-500">
            {player.team_name} &middot; {player.league}
          </p>
        </div>
        {player.role_label && <PlayerBadge role={player.role_label} />}
      </div>

      <div className="mt-3 flex flex-wrap gap-3 text-xs text-gray-600">
        <span>Age {player.age}</span>
        <span>{player.minutes_played} min</span>
        <span>{player.matches_played} matches</span>
        {player.primary_position && (
          <span className="rounded bg-gray-100 px-2 py-0.5">{player.primary_position}</span>
        )}
      </div>
    </Link>
  );
}
