// Mirrors the Pydantic schemas in backend/app/schemas/

export interface PlayerCard {
  player_season_id: number;
  player_id: number;
  player_name: string;
  team_name: string;
  league: string;
  age: number;
  minutes_played: number;
  matches_played: number;
  primary_position: string | null;
  role_label: string | null;
  role_confidence: number | null;
}

export interface PlayerSearchResponse {
  results: PlayerCard[];
  total: number;
}

export interface FeatureValues {
  [key: string]: number;
}

export interface DimensionScore {
  dimension: string;
  percentile: number;
}

export interface PlayerProfile {
  player_season_id: number;
  player_id: number;
  player_name: string;
  team_name: string;
  league: string;
  season: string;
  age: number;
  minutes_played: number;
  matches_played: number;
  primary_position: string | null;
  role_label: string | null;
  role_confidence: number | null;
  role_summary: string | null;
  features: FeatureValues;
  dimension_scores: DimensionScore[];
  radar_axes: string[] | null;
}

export interface SimilarityRequest {
  k?: number;
  league_filter?: string | null;
  age_min?: number | null;
  age_max?: number | null;
  min_minutes?: number;
  role_filter?: boolean;
  feature_weights?: Record<string, number> | null;
}

export interface SimilarPlayerResult {
  player_season_id: number;
  player_id: number;
  player_name: string;
  team_name: string;
  league: string;
  age: number;
  minutes_played: number;
  role_label: string | null;
  similarity_score: number;
  dimension_scores?: Record<string, number>;
}

export interface SimilarityResponse {
  query_player_id: number;
  query_player_name: string;
  query_role: string | null;
  results: SimilarPlayerResult[];
  total: number;
}

export interface FeatureContribution {
  feature: string;
  dimension: string;
  contribution: number;
  query_value: number;
  target_value: number;
}

export interface ExplanationResponse {
  query_player_id: number;
  target_player_id: number;
  overall_similarity: number;
  dimension_similarities: Record<string, number>;
  top_contributions: FeatureContribution[];
}

export interface ShortlistEntry {
  id: number;
  player_season_id: number;
  player_name: string;
  team_name: string;
  league: string;
  role_label: string | null;
  notes: string;
  created_at: string;
}

export interface ShortlistResponse {
  entries: ShortlistEntry[];
  total: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}
