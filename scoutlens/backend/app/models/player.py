"""Player, PlayerSeason, PlayerFeature, and PlayerVector ORM models."""

from sqlalchemy import (
    ARRAY,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Player(Base):
    __tablename__ = "players"

    player_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_name: Mapped[str] = mapped_column(String(200), nullable=False)
    nationality: Mapped[str | None] = mapped_column(String(100))
    date_of_birth = mapped_column(Date, nullable=True)
    primary_position: Mapped[str | None] = mapped_column(String(50))

    seasons: Mapped[list["PlayerSeason"]] = relationship(back_populates="player")


class PlayerSeason(Base):
    __tablename__ = "player_seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.player_id"))
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.team_id"))
    season: Mapped[str] = mapped_column(String(10), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    minutes_played: Mapped[int] = mapped_column(Integer, nullable=False)
    matches_played: Mapped[int] = mapped_column(Integer, nullable=False)
    role_label: Mapped[str | None] = mapped_column(String(50))
    role_confidence: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (UniqueConstraint("player_id", "season"),)

    player: Mapped["Player"] = relationship(back_populates="seasons")
    team: Mapped["Team | None"] = relationship(back_populates="player_seasons")
    features: Mapped["PlayerFeature | None"] = relationship(back_populates="player_season")
    vector: Mapped["PlayerVector | None"] = relationship(back_populates="player_season")


class PlayerFeature(Base):
    """Per-90 feature values for a player-season. Column order matches FEATURE_NAMES."""
    __tablename__ = "player_features"

    player_season_id: Mapped[int] = mapped_column(
        ForeignKey("player_seasons.id"), primary_key=True,
    )

    # Dim 1: Attacking (7)
    xg_per90: Mapped[float] = mapped_column(Float)
    shots_per90: Mapped[float] = mapped_column(Float)
    shots_on_target_per90: Mapped[float] = mapped_column(Float)
    goals_per90: Mapped[float] = mapped_column(Float)
    npxg_per90: Mapped[float] = mapped_column(Float)
    touches_in_box_per90: Mapped[float] = mapped_column(Float)
    xg_per_shot: Mapped[float] = mapped_column(Float)

    # Dim 2: Chance Creation (7)
    xa_per90: Mapped[float] = mapped_column(Float)
    key_passes_per90: Mapped[float] = mapped_column(Float)
    assists_per90: Mapped[float] = mapped_column(Float)
    passes_into_box_per90: Mapped[float] = mapped_column(Float)
    through_balls_per90: Mapped[float] = mapped_column(Float)
    progressive_passes_per90: Mapped[float] = mapped_column(Float)
    crosses_per90: Mapped[float] = mapped_column(Float)

    # Dim 3: Passing (7)
    passes_attempted_per90: Mapped[float] = mapped_column(Float)
    pass_completion_pct: Mapped[float] = mapped_column(Float)
    progressive_pass_distance_per90: Mapped[float] = mapped_column(Float)
    long_passes_per90: Mapped[float] = mapped_column(Float)
    long_pass_completion_pct: Mapped[float] = mapped_column(Float)
    switches_per90: Mapped[float] = mapped_column(Float)
    passes_under_pressure_pct: Mapped[float] = mapped_column(Float)

    # Dim 4: Carrying (7)
    progressive_carries_per90: Mapped[float] = mapped_column(Float)
    carry_distance_per90: Mapped[float] = mapped_column(Float)
    progressive_carry_distance_per90: Mapped[float] = mapped_column(Float)
    carries_into_box_per90: Mapped[float] = mapped_column(Float)
    dribbles_attempted_per90: Mapped[float] = mapped_column(Float)
    dribble_success_pct: Mapped[float] = mapped_column(Float)
    ball_receipts_per90: Mapped[float] = mapped_column(Float)

    # Dim 5: Defending (8)
    pressures_per90: Mapped[float] = mapped_column(Float)
    pressure_success_pct: Mapped[float] = mapped_column(Float)
    tackles_per90: Mapped[float] = mapped_column(Float)
    tackle_success_pct: Mapped[float] = mapped_column(Float)
    interceptions_per90: Mapped[float] = mapped_column(Float)
    blocks_per90: Mapped[float] = mapped_column(Float)
    ball_recoveries_per90: Mapped[float] = mapped_column(Float)
    clearances_per90: Mapped[float] = mapped_column(Float)

    # Dim 6: Aerial / Physical (6)
    aerial_duels_per90: Mapped[float] = mapped_column(Float)
    aerial_win_pct: Mapped[float] = mapped_column(Float)
    ground_duels_per90: Mapped[float] = mapped_column(Float)
    ground_duel_win_pct: Mapped[float] = mapped_column(Float)
    fouls_won_per90: Mapped[float] = mapped_column(Float)
    dispossessed_per90: Mapped[float] = mapped_column(Float)

    player_season: Mapped["PlayerSeason"] = relationship(back_populates="features")


class PlayerVector(Base):
    """Normalised 42-d vector + optional UMAP 2D projection."""
    __tablename__ = "player_vectors"

    player_season_id: Mapped[int] = mapped_column(
        ForeignKey("player_seasons.id"), primary_key=True,
    )
    vector: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)
    umap_x: Mapped[float | None] = mapped_column(Float)
    umap_y: Mapped[float | None] = mapped_column(Float)

    player_season: Mapped["PlayerSeason"] = relationship(back_populates="vector")


# Avoid circular import — Team is referenced above via string annotations
from app.models.team import Team  # noqa: E402, F401
