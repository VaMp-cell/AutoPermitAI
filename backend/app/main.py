"""
AutoPermit AI — FastAPI Application Entry Point
Initializes the app, loads ML models, and configures middleware.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.routes import router
from app.services.vision_service import VisionService
from app.services.ocr_service import OCRService
from app.services.compliance_service import ComplianceService
from app.services.storage_service import StorageService
from app.services.regulation_service import RegulationService

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("autopermit")

# ── Service Singletons ───────────────────────────────────────────────────────
vision_service = VisionService(model_path=settings.YOLO_MODEL_PATH)
ocr_service = OCRService()
compliance_service = ComplianceService()
storage_service = StorageService()
regulation_service = RegulationService(regulation_path=settings.REGULATION_FILE)


# ── App Lifespan ──────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / shutdown lifecycle.
    Loads heavy resources (YOLOv8 model) once at startup.
    """
    logger.info("=" * 60)
    logger.info("  AutoPermit AI — Starting Up")
    logger.info("=" * 60)

    # Create required directories
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    # Load YOLOv8 model
    try:
        vision_service.load_model()
        logger.info("✓ Vision service ready")
    except Exception as e:
        logger.error(f"✗ Failed to load YOLO model: {e}")
        logger.warning("  Vision detection will not be available")

    # Initialize compliance client
    compliance_service.initialize()
    if compliance_service.provider != "MOCK":
        logger.info(f"✓ Compliance service ready ({compliance_service.provider})")
    else:
        logger.warning("✓ Compliance service in MOCK mode (no API key)")

    # OCR is lazy-loaded on first use
    logger.info("✓ OCR service ready (lazy-loaded)")

    logger.info("=" * 60)
    logger.info(f"  Server: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"  Docs:   http://{settings.HOST}:{settings.PORT}/docs")
    logger.info("=" * 60)

    yield  # ← App is running

    # Shutdown
    logger.info("AutoPermit AI — Shutting Down")


# ── FastAPI App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="AutoPermit AI",
    description=(
        "Automated Municipal Building Permit Verification System. "
        "Uses YOLOv8 for structural element detection and GPT-4o for "
        "building code compliance analysis."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static file serving for output images ─────────────────────────────────────
# Mount after directories are created in lifespan
# We use the /image/ route in routes.py instead for more control

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(router, prefix="")


# ── Health Check ──────────────────────────────────────────────────────────────


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AutoPermit AI",
        "version": "1.0.0",
        "vision_model_loaded": vision_service.model is not None,
        "llm_configured": compliance_service.client is not None,
        "reports_stored": storage_service.count,
    }


# ── Run with: uvicorn app.main:app --reload ──────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
    )
