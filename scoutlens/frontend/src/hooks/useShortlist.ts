import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "../api/client";
import type { ShortlistResponse, ShortlistEntry } from "../types";

export function useShortlist() {
  return useQuery({
    queryKey: ["shortlist"],
    queryFn: async () => {
      const { data } = await api.get<ShortlistResponse>("/shortlist");
      return data;
    },
    staleTime: 30_000,
  });
}

export function useAddToShortlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: { player_season_id: number; notes?: string }) => {
      const { data } = await api.post<ShortlistEntry>("/shortlist", body);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["shortlist"] }),
  });
}

export function useUpdateShortlistNotes() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, notes }: { id: number; notes: string }) => {
      const { data } = await api.patch<ShortlistEntry>(`/shortlist/${id}`, { notes });
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["shortlist"] }),
  });
}

export function useRemoveFromShortlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/shortlist/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["shortlist"] }),
  });
}
