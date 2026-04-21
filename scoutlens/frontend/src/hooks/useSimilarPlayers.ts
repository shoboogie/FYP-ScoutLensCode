import { useMutation } from "@tanstack/react-query";
import api from "../api/client";
import type { SimilarityRequest, SimilarityResponse } from "../types";

export function useSimilarPlayers(playerSeasonId: number) {
  return useMutation({
    mutationFn: async (body: SimilarityRequest) => {
      const { data } = await api.post<SimilarityResponse>(
        `/similar/${playerSeasonId}`,
        body
      );
      return data;
    },
  });
}
