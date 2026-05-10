"""
AutoPermit AI — API Routes
All HTTP endpoints for the permit verification system.
"""

from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import settings
from app.schemas import (
    AnalyzeRequest,
    ComplianceReport,
    ReportListItem,
    UploadResponse,
    RegulationSearchRequest,
    RegulationSearchResult,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ── File metadata store (maps file_id → info) ────────────────────────────────
_uploaded_files: dict[str, dict] = {}


def _get_services():
    """Import services lazily to avoid circular imports at module level."""
    from app.main import vision_service, ocr_service, compliance_service, storage_service, regulation_service
    return vision_service, ocr_service, compliance_service, storage_service, regulation_service


# ── POST /upload ──────────────────────────────────────────────────────────────


@router.post("/upload", response_model=UploadResponse, tags=["Blueprint"])
async def upload_blueprint(file: UploadFile = File(...)):
    """
    Upload an architectural blueprint PDF.
    Returns a file_id for use with the /analyze endpoint.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Generate unique file ID
    file_id = str(uuid.uuid4())
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Save uploaded PDF
    file_path = upload_dir / f"{file_id}.pdf"
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")

    # Get page count via PyMuPDF
    try:
        import fitz
        doc = fitz.open(str(file_path))
        page_count = len(doc)
        doc.close()
    except Exception:
        page_count = 1

    # Store metadata
    _uploaded_files[file_id] = {
        "filename": file.filename,
        "path": str(file_path),
        "page_count": page_count,
    }

    logger.info(f"Uploaded: {file.filename} → {file_id} ({page_count} pages)")

    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        page_count=page_count,
    )


# ── POST /analyze ────────────────────────────────────────────────────────────


@router.post("/analyze", response_model=ComplianceReport, tags=["Analysis"])
async def analyze_blueprint(request: AnalyzeRequest):
    """
    Run the full analysis pipeline on an uploaded blueprint:
    1. PDF → Image conversion
    2. YOLOv8 object detection
    3. PaddleOCR dimension extraction
    4. GPT-4o compliance analysis
    """
    vision_service, ocr_service, compliance_service, storage_service = _get_services()

    file_info = _uploaded_files.get(request.file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found. Upload a PDF first.")

    pdf_path = file_info["path"]
    report_id = str(uuid.uuid4())

    # Create output directory for this report
    output_dir = Path(settings.OUTPUT_DIR) / report_id
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1 & 2: PDF → Image → YOLOv8 Detection
        logger.info(f"[{report_id}] Starting vision pipeline...")
        original_img, annotated_img, detections = vision_service.process_blueprint(
            pdf_path=pdf_path,
            output_dir=output_dir,
        )

        # Step 3: OCR Dimension Extraction
        logger.info(f"[{report_id}] Running OCR extraction...")
        ocr_results = ocr_service.extract_dimensions(original_img)
        ocr_formatted = ocr_service.format_for_llm(ocr_results)

        # Step 4: LLM Compliance Analysis
        logger.info(f"[{report_id}] Running compliance analysis...")
        raw_result = compliance_service.analyze(
            detections=detections,
            ocr_results=ocr_results,
            ocr_formatted=ocr_formatted,
        )

        # Parse and validate compliance checks
        compliance_checks = compliance_service.parse_compliance_checks(raw_result)
        overall_status = raw_result.get("overall_status", "NEEDS_REVIEW")
        summary = raw_result.get("summary", "Analysis complete.")

        # Build the report
        report = ComplianceReport(
            report_id=report_id,
            filename=file_info["filename"],
            image_url=f"/image/{report_id}",
            page_count=file_info["page_count"],
            detections=detections,
            ocr_results=ocr_results,
            compliance_checks=compliance_checks,
            overall_status=overall_status,
            summary=summary,
        )

        # Store report
        storage_service.save_report(report)

        logger.info(
            f"[{report_id}] Analysis complete — "
            f"{len(detections)} detections, "
            f"{len(compliance_checks)} checks, "
            f"status: {overall_status}"
        )

        return report

    except Exception as e:
        logger.error(f"[{report_id}] Pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ── GET /report/{id} ─────────────────────────────────────────────────────────


@router.get("/report/{report_id}", response_model=ComplianceReport, tags=["Reports"])
async def get_report(report_id: str):
    """Retrieve a compliance report by ID."""
    _, _, _, storage_service = _get_services()

    report = storage_service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


# ── GET /reports ──────────────────────────────────────────────────────────────


@router.get("/reports", response_model=list[ReportListItem], tags=["Reports"])
async def list_reports():
    """List all compliance reports."""
    _, _, _, storage_service = _get_services()
    return storage_service.list_reports()


# ── GET /image/{report_id} ───────────────────────────────────────────────────


@router.get("/image/{report_id}", tags=["Assets"])
async def get_image(report_id: str, annotated: bool = True):
    """
    Serve the blueprint image for a report.

    Args:
        report_id: The report ID.
        annotated: If True (default), return the annotated image with bounding boxes.
    """
    filename = "annotated.jpg" if annotated else "original.jpg"
    image_path = Path(settings.OUTPUT_DIR) / report_id / filename

    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(str(image_path), media_type="image/jpeg")


# ── GET /regulations/search ──────────────────────────────────────────────────


@router.post("/regulations/search", response_model=list[RegulationSearchResult], tags=["Regulations"])
async def search_regulations(request: RegulationSearchRequest):
    """Search the building regulations for relevant sections."""
    _, _, _, _, regulation_service = _get_services()
    results = regulation_service.search(query=request.query, limit=request.limit)
    return results
