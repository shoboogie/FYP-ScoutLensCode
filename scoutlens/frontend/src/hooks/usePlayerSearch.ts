import { useQuery } from "@tanstack/react-query";
import api from "../api/client";
import type { PlayerSearchResponse } from "../types";

interface SearchParams {
  q: string;
  league?: string;
  position?: string;
  minMinutes?: number;
}

export function usePlayerSearch(params: SearchParams) {
  return useQuery({
    queryKey: ["playerSearch", params],
    queryFn: async () => {
      const { data } = await api.get<PlayerSearchResponse>("/search", {
        params: {
          q: params.q,
          league: params.league || undefined,
          position: params.position || undefined,
          min_minutes: params.minMinutes || 900,
        },
      });
      return data;
    },
    enabled: params.q.length >= 2,
    staleTime: 60_000,
  });
}
