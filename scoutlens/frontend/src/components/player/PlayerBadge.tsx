interface Props {
  role: string;
}

const ROLE_COLOURS: Record<string, string> = {
  "Ball-Playing CB": "bg-blue-100 text-blue-800",
  "Aerial/Stopper CB": "bg-blue-200 text-blue-900",
  "Attacking Full-Back": "bg-cyan-100 text-cyan-800",
  "Inverted Full-Back": "bg-cyan-200 text-cyan-900",
  "Deep-Lying Playmaker": "bg-indigo-100 text-indigo-800",
  "Ball-Winning Midfielder": "bg-red-100 text-red-800",
  "Box-to-Box Midfielder": "bg-orange-100 text-orange-800",
  "Advanced Playmaker": "bg-purple-100 text-purple-800",
  "Inside Forward": "bg-pink-100 text-pink-800",
  "Touchline Winger": "bg-green-100 text-green-800",
  "Complete Forward": "bg-amber-100 text-amber-800",
  "Poacher": "bg-rose-100 text-rose-800",
  "Target Forward": "bg-yellow-100 text-yellow-800",
  "Pressing Forward": "bg-emerald-100 text-emerald-800",
};

export default function PlayerBadge({ role }: Props) {
  const colour = ROLE_COLOURS[role] ?? "bg-gray-100 text-gray-700";

  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${colour}`}>
      {role}
    </span>
  );
}
