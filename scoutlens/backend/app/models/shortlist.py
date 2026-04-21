"""Shortlist ORM model — user's saved player-season entries with notes."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Shortlist(Base):
    __tablename__ = "shortlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    player_season_id: Mapped[int] = mapped_column(ForeignKey("player_seasons.id"))
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(),
    )

    __table_args__ = (UniqueConstraint("user_id", "player_season_id"),)

    user: Mapped["User"] = relationship(back_populates="shortlists")
    player_season: Mapped["PlayerSeason"] = relationship()


from app.models.user import User  # noqa: E402, F401
from app.models.player import PlayerSeason  # noqa: E402, F401
