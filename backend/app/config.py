"""
AutoPermit AI — Configuration
Loads environment variables via pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from dotenv import load_dotenv
import os

# Explicitly load .env from the current directory
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # ── LLM ──────────────────────────────────────────────
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

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
    TESSERACT_CMD: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    # ── Server ───────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    @property
    def cors_origin_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]




settings = Settings()
