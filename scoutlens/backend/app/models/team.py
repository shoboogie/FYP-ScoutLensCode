"""Team ORM model."""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Team(Base):
    __tablename__ = "teams"

    team_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_name: Mapped[str] = mapped_column(String(200), nullable=False)
    league: Mapped[str] = mapped_column(String(100), nullable=False)
    season: Mapped[str] = mapped_column(String(10), nullable=False)

    player_seasons: Mapped[list["PlayerSeason"]] = relationship(back_populates="team")


from app.models.player import PlayerSeason  # noqa: E402, F401
