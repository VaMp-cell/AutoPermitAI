"""
AutoPermit AI — Configuration
Loads environment variables via pydantic-settings.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # ── LLM ──────────────────────────────────────────────
    OPENAI_API_KEY: str = ""

    # ── YOLOv8 ───────────────────────────────────────────
    YOLO_MODEL_PATH: str = "yolov8n.pt"

    # ── File Storage ─────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    REGULATION_FILE: str = "regulations/goa_building_regulations_2010.txt"

    # ── Supabase (optional) ──────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # ── CORS ─────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000"

    # ── Server ───────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    @property
    def cors_origin_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
