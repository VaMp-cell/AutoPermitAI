"""
AutoPermit AI — Pydantic Schemas
Defines all request/response models shared between services and the API layer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ── Detection Models ─────────────────────────────────────────────────────────


class DetectionBox(BaseModel):
    """A single object detected by YOLOv8 on the blueprint."""

    label: str = Field(..., description="Class label, e.g. 'fire_exit', 'staircase', 'parking'")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score")
    x: float = Field(..., ge=0.0, le=1.0, description="Normalized x-coordinate of box center")
    y: float = Field(..., ge=0.0, le=1.0, description="Normalized y-coordinate of box center")
    width: float = Field(..., ge=0.0, le=1.0, description="Normalized width of bounding box")
    height: float = Field(..., ge=0.0, le=1.0, description="Normalized height of bounding box")


# ── OCR Models ───────────────────────────────────────────────────────────────


class OCRExtraction(BaseModel):
    """A text region extracted by PaddleOCR with optional numeric parsing."""

    text: str = Field(..., description="Raw OCR text")
    value: Optional[float] = Field(None, description="Parsed numeric value (e.g. 3.5)")
    unit: Optional[str] = Field(None, description="Measurement unit (e.g. 'm', 'ft', 'in')")
    location: dict = Field(default_factory=dict, description="Bounding box coordinates of the text")


# ── Compliance Models ────────────────────────────────────────────────────────


class ComplianceCheck(BaseModel):
    """A single compliance evaluation from the LLM engine."""

    code_reference: str = Field(..., description="Building code section, e.g. 'IBC Section 1006.3'")
    requirement: str = Field(..., description="Human-readable requirement description")
    status: Literal["PASS", "FAIL", "WARNING", "NOT_FOUND"] = Field(
        ..., description="Compliance status"
    )
    severity: Literal["Critical", "Major", "Minor"] = Field(
        ..., description="Severity level of this check"
    )
    reasoning: str = Field(..., description="LLM chain-of-thought explanation")
    detected_value: Optional[str] = Field(None, description="What was found on the blueprint")
    required_value: Optional[str] = Field(None, description="What the code requires")


class ComplianceReport(BaseModel):
    """Full compliance report combining vision, OCR, and LLM analysis."""

    report_id: str = Field(..., description="Unique identifier for this report")
    filename: str = Field(..., description="Original uploaded filename")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    image_url: str = Field("", description="URL/path to the processed blueprint image")
    page_count: int = Field(1, description="Number of pages in the PDF")
    detections: list[DetectionBox] = Field(default_factory=list)
    ocr_results: list[OCRExtraction] = Field(default_factory=list)
    compliance_checks: list[ComplianceCheck] = Field(default_factory=list)
    overall_status: Literal["APPROVED", "REJECTED", "NEEDS_REVIEW"] = Field(
        "NEEDS_REVIEW", description="Aggregate compliance status"
    )
    summary: str = Field("", description="Executive summary from the LLM")


# ── Request / Response Helpers ───────────────────────────────────────────────


class UploadResponse(BaseModel):
    """Returned after a PDF is successfully uploaded."""

    file_id: str
    filename: str
    page_count: int
    message: str = "File uploaded successfully"


class AnalyzeRequest(BaseModel):
    """Request body for the /analyze endpoint."""

    file_id: str


class ReportListItem(BaseModel):
    """Lightweight report entry for listing."""

    report_id: str
    filename: str
    created_at: datetime
    overall_status: Literal["APPROVED", "REJECTED", "NEEDS_REVIEW"]
    detection_count: int = 0
    check_count: int = 0


# ── Regulation Search Models ──────────────────────────────────────────────────


class RegulationSearchRequest(BaseModel):
    """Request body for the /regulations/search endpoint."""

    query: str
    limit: int = 5


class RegulationSearchResult(BaseModel):
    """A single result from the regulation search."""

    id: int
    title: str
    content: str
    score: float
