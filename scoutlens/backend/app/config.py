"""Application configuration loaded from environment variables via .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """ScoutLens configuration.

    Values are read from environment variables (or .env file at project root).
    Docker Compose can override any setting via its ``environment:`` block.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://scoutlens:scoutlens@localhost:5432/scoutlens"
    database_url_sync: str = "postgresql://scoutlens:scoutlens@localhost:5432/scoutlens"

    # JWT authentication
    jwt_secret_key: str = "change-me-to-a-random-256-bit-string"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # Model / index paths
    faiss_index_path: str = "data/models/faiss_index.bin"
    scaler_path: str = "data/models/scaler.pkl"
    player_map_path: str = "data/models/player_id_map.npy"

    # CORS
    allowed_origins: str = "http://localhost:5173"

    # Admin
    admin_email: str = "admin@scoutlens.local"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [o.strip() for o in self.allowed_origins.split(",")]


settings = Settings()
