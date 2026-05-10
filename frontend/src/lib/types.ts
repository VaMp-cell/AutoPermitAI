/* ── AutoPermit AI — TypeScript Types ──────────────────────────
 * These mirror the Pydantic schemas in the backend.
 * ──────────────────────────────────────────────────────────── */

export interface DetectionBox {
  label: string;
  confidence: number;
  x: number; // Normalized 0-1
  y: number;
  width: number;
  height: number;
}

export interface OCRExtraction {
  text: string;
  value: number | null;
  unit: string | null;
  location: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
    confidence: number;
  };
}

export type ComplianceStatus = "PASS" | "FAIL" | "WARNING" | "NOT_FOUND";
export type SeverityLevel = "Critical" | "Major" | "Minor";
export type OverallStatus = "APPROVED" | "REJECTED" | "NEEDS_REVIEW";

export interface ComplianceCheck {
  code_reference: string;
  requirement: string;
  status: ComplianceStatus;
  severity: SeverityLevel;
  reasoning: string;
  detected_value: string | null;
  required_value: string | null;
}

export interface ComplianceReport {
  report_id: string;
  filename: string;
  created_at: string;
  image_url: string;
  page_count: number;
  detections: DetectionBox[];
  ocr_results: OCRExtraction[];
  compliance_checks: ComplianceCheck[];
  overall_status: OverallStatus;
  summary: string;
}

export interface UploadResponse {
  file_id: string;
  filename: string;
  page_count: number;
  message: string;
}

export interface ReportListItem {
  report_id: string;
  filename: string;
  created_at: string;
  overall_status: OverallStatus;
  detection_count: number;
  check_count: number;
}

/** Processing pipeline stages */
export type PipelineStage =
  | "idle"
  | "uploading"
  | "converting"
  | "detecting"
  | "ocr"
  | "analyzing"
  | "complete"
  | "error";
