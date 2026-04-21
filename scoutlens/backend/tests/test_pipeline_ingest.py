"""Tests for pipeline Steps 1–4.

These tests require the pipeline to have been run at least once so that
cached parquet files exist in data/raw/ and data/processed/.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

DATA_DIR = Path(__file__).resolve().parents[1].parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

EXPECTED_LEAGUES = [
    "premier_league",
    "la_liga",
    "bundesliga",
    "serie_a",
    "ligue_1",
]


# ── Step 1: Ingestion tests ──────────────────────────────────────────


class TestIngestion:
    """Verify raw parquet files exist and contain expected columns."""

    def test_event_parquets_exist(self) -> None:
        for league in EXPECTED_LEAGUES:
            path = RAW_DIR / f"events_{league}.parquet"
            assert path.exists(), f"Missing events parquet for {league}"

    def test_match_parquets_exist(self) -> None:
        for league in EXPECTED_LEAGUES:
            path = RAW_DIR / f"matches_{league}.parquet"
            assert path.exists(), f"Missing matches parquet for {league}"

    def test_lineups_parquet_exists(self) -> None:
        path = RAW_DIR / "lineups_all.parquet"
        assert path.exists(), "Missing lineups parquet"

    def test_events_have_expected_columns(self) -> None:
        """Check that at least one events parquet has key StatsBomb columns."""
        path = RAW_DIR / "events_premier_league.parquet"
        if not path.exists():
            pytest.skip("Premier League events not yet ingested")
        df = pd.read_parquet(path)
        # Raw parquets use short names; normalisation renames them
        required = ["type", "player_id", "player", "match_id", "minute"]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_events_row_count_reasonable(self) -> None:
        """Each league should have at least 500k events."""
        for league in EXPECTED_LEAGUES:
            path = RAW_DIR / f"events_{league}.parquet"
            if not path.exists():
                pytest.skip(f"{league} not yet ingested")
            df = pd.read_parquet(path)
            assert len(df) > 500_000, (
                f"{league} has only {len(df)} events — expected >500k"
            )

    def test_matches_count(self) -> None:
        """Verify match counts per league."""
        expected_min = {
            "premier_league": 370,
            "la_liga": 370,
            "bundesliga": 300,
            "serie_a": 370,
            "ligue_1": 370,
        }
        for league, min_matches in expected_min.items():
            path = RAW_DIR / f"matches_{league}.parquet"
            if not path.exists():
                pytest.skip(f"{league} matches not yet ingested")
            df = pd.read_parquet(path)
            assert len(df) >= min_matches, (
                f"{league} has only {len(df)} matches — expected >={min_matches}"
            )


# ── Step 2: Normalisation tests ──────────────────────────────────────


class TestNormalisation:
    """Verify normalised events have split location columns."""

    @pytest.fixture()
    def events(self) -> pd.DataFrame:
        path = PROCESSED_DIR / "events_normalised.parquet"
        if not path.exists():
            pytest.skip("Normalised events not yet created")
        return pd.read_parquet(path)

    def test_location_xy_columns_exist(self, events: pd.DataFrame) -> None:
        assert "location_x" in events.columns
        assert "location_y" in events.columns

    def test_pass_end_location_split(self, events: pd.DataFrame) -> None:
        assert "pass_end_location_x" in events.columns
        assert "pass_end_location_y" in events.columns

    def test_carry_end_location_split(self, events: pd.DataFrame) -> None:
        assert "carry_end_location_x" in events.columns
        assert "carry_end_location_y" in events.columns

    def test_no_list_columns_remain(self, events: pd.DataFrame) -> None:
        """No column should contain Python lists."""
        # Check unsplit location columns are gone
        for col in ["location", "pass_end_location", "carry_end_location"]:
            assert col not in events.columns, f"Unsplit column remains: {col}"

    def test_league_column_present(self, events: pd.DataFrame) -> None:
        assert "league" in events.columns
        assert events["league"].nunique() == 5

    def test_row_count(self, events: pd.DataFrame) -> None:
        """Combined events should have >3M rows across 5 leagues."""
        assert len(events) > 3_000_000


# ── Step 3: Minutes computation tests ────────────────────────────────


class TestMinutesComputation:
    """Verify per-player per-match minutes are reasonable."""

    @pytest.fixture()
    def minutes(self) -> pd.DataFrame:
        path = PROCESSED_DIR / "player_minutes.parquet"
        if not path.exists():
            pytest.skip("Player minutes not yet computed")
        return pd.read_parquet(path)

    def test_no_negative_minutes(self, minutes: pd.DataFrame) -> None:
        assert (minutes["minutes_played"] >= 0).all()

    def test_max_minutes_reasonable(self, minutes: pd.DataFrame) -> None:
        """No single match appearance should exceed 130 minutes."""
        assert minutes["minutes_played"].max() <= 130

    def test_required_columns(self, minutes: pd.DataFrame) -> None:
        required = [
            "player_id", "player_name", "match_id",
            "team_name", "league", "minutes_played", "started",
        ]
        for col in required:
            assert col in minutes.columns, f"Missing column: {col}"

    def test_team_match_totals_reasonable(self, minutes: pd.DataFrame) -> None:
        """Per-team per-match totals should average ~1000 (11 x ~90)."""
        totals = minutes.groupby(["match_id", "team_name"])["minutes_played"].sum()
        mean_total = totals.mean()
        assert 800 < mean_total < 1200, (
            f"Mean team-match total is {mean_total:.0f} — expected ~990"
        )


# ── Step 4: Quality filter tests ─────────────────────────────────────


class TestQualityFilter:
    """Verify qualified players meet all eligibility criteria."""

    @pytest.fixture()
    def players(self) -> pd.DataFrame:
        path = PROCESSED_DIR / "qualified_players.parquet"
        if not path.exists():
            pytest.skip("Qualified players not yet generated")
        return pd.read_parquet(path)

    def test_no_goalkeepers(self, players: pd.DataFrame) -> None:
        gks = players[players["primary_position"] == "Goalkeeper"]
        assert len(gks) == 0, f"Found {len(gks)} goalkeepers in qualified players"

    def test_minimum_minutes(self, players: pd.DataFrame) -> None:
        below = players[players["total_minutes"] < 900]
        assert len(below) == 0, (
            f"Found {len(below)} players with <900 minutes"
        )

    def test_player_count_range(self, players: pd.DataFrame) -> None:
        """Expected ~1,500–1,800 qualified outfield player-seasons."""
        count = len(players)
        assert 1000 <= count <= 2200, (
            f"Qualified player count {count} outside expected range [1000, 2200]"
        )

    def test_all_five_leagues_represented(self, players: pd.DataFrame) -> None:
        leagues = players["league"].unique()
        assert len(leagues) == 5, f"Only {len(leagues)} leagues represented"

    def test_required_columns(self, players: pd.DataFrame) -> None:
        required = [
            "player_id", "player_name", "team_name", "league",
            "season", "total_minutes", "matches_played", "primary_position",
        ]
        for col in required:
            assert col in players.columns, f"Missing column: {col}"
