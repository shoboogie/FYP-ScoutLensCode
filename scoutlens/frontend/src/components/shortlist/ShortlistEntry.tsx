import { Link } from "react-router-dom";
import type { ShortlistEntry as ShortlistEntryType } from "../../types";
import PlayerBadge from "../player/PlayerBadge";

interface Props {
  entry: ShortlistEntryType;
  onRemove: (id: number) => void;
  onEditNotes: (id: number, notes: string) => void;
}

export default function ShortlistEntryCard({ entry, onRemove }: Props) {
  return (
    <div className="rounded-lg bg-white p-4 shadow">
      <div className="flex items-start justify-between">
        <div>
          <Link
            to={`/player/${entry.player_season_id}`}
            className="text-lg font-semibold text-navy hover:text-teal transition-colors"
          >
            {entry.player_name}
          </Link>
          <p className="text-sm text-gray-500">
            {entry.team_name} &middot; {entry.league}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {entry.role_label && <PlayerBadge role={entry.role_label} />}
          <button
            onClick={() => onRemove(entry.id)}
            className="rounded px-2 py-1 text-xs text-red-500 hover:bg-red-50 transition-colors"
          >
            Remove
          </button>
        </div>
      </div>

      {entry.notes && (
        <p className="mt-2 rounded bg-gray-50 px-3 py-2 text-sm text-gray-700 italic">
          {entry.notes}
        </p>
      )}

      <div className="mt-2 text-xs text-gray-400">
        Added {new Date(entry.created_at).toLocaleDateString("en-GB")}
      </div>
    </div>
  );
}
