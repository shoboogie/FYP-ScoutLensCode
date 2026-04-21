import { useQuery } from "@tanstack/react-query";
import api from "../api/client";
import type { PlayerProfile } from "../types";

export function usePlayerProfile(playerSeasonId: number | undefined) {
  return useQuery({
    queryKey: ["playerProfile", playerSeasonId],
    queryFn: async () => {
      const { data } = await api.get<PlayerProfile>(`/player/${playerSeasonId}`);
      return data;
    },
    enabled: !!playerSeasonId,
    staleTime: 300_000,
  });
}
