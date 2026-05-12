"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import BlueprintViewer from "@/components/blueprint-viewer";
import ComplianceChecklist from "@/components/compliance-checklist";
import { getReport, getImageUrl } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { ComplianceReport } from "@/lib/types";
import {
  ArrowLeft,
  FileText,
  Download,
  Clock,
  Layers,
  ScanSearch,
  CheckCircle2,
  Loader2,
} from "lucide-react";

export default function ReportPage() {
  const params = useParams();
  const reportId = params.id as string;

  const [report, setReport] = useState<ComplianceReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!reportId) return;

    getReport(reportId)
      .then(setReport)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load report")
      )
      .finally(() => setLoading(false));
  }, [reportId]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading report...</p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="glass-card rounded-2xl p-8 text-center max-w-md">
          <p className="text-sm text-rose-400 font-medium">
            {error || "Report not found"}
          </p>
          <Link
            href="/"
            className="mt-4 inline-flex items-center gap-2 text-xs text-primary hover:underline"
          >
            <ArrowLeft className="h-3 w-3" /> Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors mb-4"
        >
          <ArrowLeft className="h-3 w-3" /> Back to Dashboard
        </Link>

        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/15">
              <FileText className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-foreground">
                {report.filename}
              </h1>
              <div className="mt-1 flex flex-wrap items-center gap-3 text-[10px] text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatDate(report.created_at)}
                </span>
                <span className="flex items-center gap-1">
                  <Layers className="h-3 w-3" />
                  {report.page_count} page(s)
                </span>
                <span className="flex items-center gap-1">
                  <ScanSearch className="h-3 w-3" />
                  {report.detections.length} detections
                </span>
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3" />
                  {report.compliance_checks.length} compliance checks
                </span>
              </div>
            </div>
          </div>

          <button 
            onClick={() => {
              const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
              const downloadAnchorNode = document.createElement('a');
              downloadAnchorNode.setAttribute("href",     dataStr);
              downloadAnchorNode.setAttribute("download", `report_${report.report_id}.json`);
              document.body.appendChild(downloadAnchorNode); 
              downloadAnchorNode.click();
              downloadAnchorNode.remove();
            }}
            className="flex items-center gap-2 rounded-lg bg-primary/15 px-4 py-2 text-xs font-medium text-primary hover:bg-primary/25 transition-colors"
          >
            <Download className="h-3.5 w-3.5" />
            Export Report
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Blueprint Viewer */}
        <div className="glass-card rounded-2xl p-5">
          <h2 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
            <ScanSearch className="h-4 w-4 text-primary" />
            Blueprint Analysis
          </h2>
          <BlueprintViewer
            imageUrl={getImageUrl(report.report_id)}
            detections={report.detections}
          />
        </div>

        {/* Compliance Checklist */}
        <div className="glass-card rounded-2xl p-5">
          <h2 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-primary" />
            Compliance Report
          </h2>
          <ComplianceChecklist
            checks={report.compliance_checks}
            overallStatus={report.overall_status}
            summary={report.summary}
          />
        </div>
      </div>

      {/* OCR Results (if any) */}
      {report.ocr_results.length > 0 && (
        <div className="mt-6 glass-card rounded-2xl p-5">
          <h2 className="text-sm font-semibold text-foreground mb-4">
            Extracted Dimensions (OCR)
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
            {report.ocr_results
              .filter((r) => r.value !== null)
              .map((r, i) => (
                <div
                  key={i}
                  className="rounded-lg bg-white/[0.03] border border-white/[0.05] px-3 py-2"
                >
                  <p className="text-xs text-muted-foreground">{r.text}</p>
                  <p className="text-sm font-semibold text-foreground">
                    {r.value}
                    {r.unit ? ` ${r.unit}` : ""}
                  </p>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
