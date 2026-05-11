/* ── AutoPermit AI — API Client ────────────────────────────────
 * Fetch wrapper for all FastAPI backend endpoints.
 * ──────────────────────────────────────────────────────────── */

import type {
  ComplianceReport,
  ReportListItem,
  UploadResponse,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Generic fetch wrapper with error handling */
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const errorBody = await res.text().catch(() => "Unknown error");
    throw new Error(
      `API Error ${res.status}: ${errorBody}`
    );
  }

  return res.json();
}

// ── Endpoints ────────────────────────────────────────────────

/** Upload a PDF blueprint file */
export async function uploadBlueprint(
  file: File
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return apiFetch<UploadResponse>("/upload", {
    method: "POST",
    body: formData,
  });
}

/** Run the full analysis pipeline on an uploaded file */
export async function analyzeBlueprint(
  fileId: string,
  siteContext?: Record<string, any>
): Promise<ComplianceReport> {
  return apiFetch<ComplianceReport>("/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      file_id: fileId,
      site_context: siteContext 
    }),
  });
}

/** Get a single compliance report by ID */
export async function getReport(
  reportId: string
): Promise<ComplianceReport> {
  return apiFetch<ComplianceReport>(`/report/${reportId}`);
}

/** List all compliance reports */
export async function listReports(): Promise<ReportListItem[]> {
  return apiFetch<ReportListItem[]>("/reports");
}

/** Get the image URL for a report */
export function getImageUrl(
  reportId: string,
  annotated: boolean = true
): string {
  return `${API_BASE}/image/${reportId}?annotated=${annotated}`;
}

/** Check API health */
export async function checkHealth(): Promise<{
  status: string;
  vision_model_loaded: boolean;
  llm_configured: boolean;
  reports_stored: number;
}> {
  return apiFetch("/health");
}
