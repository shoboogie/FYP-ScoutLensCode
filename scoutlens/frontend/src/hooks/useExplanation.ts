import { useQuery } from "@tanstack/react-query";
import api from "../api/client";
import type { ExplanationResponse } from "../types";

export function useExplanation(queryId: number | undefined, targetId: number | undefined) {
  return useQuery({
    queryKey: ["explanation", queryId, targetId],
    queryFn: async () => {
      const { data } = await api.get<ExplanationResponse>(
        `/explain/${queryId}`,
        { params: { target_id: targetId } }
      );
      return data;
    },
    enabled: !!queryId && !!targetId,
    staleTime: 300_000,
  });
}
