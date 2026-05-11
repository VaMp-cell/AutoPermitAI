"use client";

import { useState, useCallback, useEffect } from "react";
import FileUploader from "@/components/file-uploader";
import BlueprintViewer from "@/components/blueprint-viewer";
import ComplianceChecklist from "@/components/compliance-checklist";
import ProcessingIndicator from "@/components/processing-indicator";
import ReportCard from "@/components/report-card";
import {
  uploadBlueprint,
  analyzeBlueprint,
  listReports,
  getImageUrl,
} from "@/lib/api";
import type {
  ComplianceReport,
  ReportListItem,
  PipelineStage,
} from "@/lib/types";
import {
  Shield,
  ScanSearch,
  CheckCircle2,
  AlertTriangle,
  Activity,
  Settings,
} from "lucide-react";

export default function DashboardPage() {
  const [stage, setStage] = useState<PipelineStage>("idle");
  const [progress, setProgress] = useState(0);
  const [report, setReport] = useState<ComplianceReport | null>(null);
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [siteContext, setSiteContext] = useState({
    zone: "S1",
    plot_area: 450,
    road_width: 6,
  });

  // Fetch existing reports on mount
  useEffect(() => {
    listReports()
      .then(setReports)
      .catch(() => {});
  }, []);

  const handleFileSelected = useCallback(async (file: File) => {
    setError(null);
    setReport(null);

    try {
      // Stage 1: Upload
      setStage("uploading");
      setProgress(10);
      const uploadRes = await uploadBlueprint(file);
      setProgress(25);

      // Stage 2-5: Analyze (backend runs the full pipeline)
      setStage("converting");
      setProgress(35);

      // Simulate stage progression while backend processes
      const stageTimer = setTimeout(() => {
        setStage("detecting");
        setProgress(50);
      }, 1500);

      const stageTimer2 = setTimeout(() => {
        setStage("ocr");
        setProgress(65);
      }, 3000);

      const stageTimer3 = setTimeout(() => {
        setStage("analyzing");
        setProgress(80);
      }, 4500);

      const result = await analyzeBlueprint(uploadRes.file_id, siteContext);

      // Clear timers if analysis finishes quickly
      clearTimeout(stageTimer);
      clearTimeout(stageTimer2);
      clearTimeout(stageTimer3);

      setProgress(100);
      setReport(result);
      setStage("complete");

      // Refresh reports list
      listReports()
        .then(setReports)
        .catch(() => {});
    } catch (err) {
      setStage("error");
      setError(
        err instanceof Error ? err.message : "An unexpected error occurred"
      );
    }
  }, []);


  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/15">
            <Shield className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Blueprint Verification
            </h1>
            <p className="text-sm text-muted-foreground">
              Upload an architectural PDF for instant compliance analysis
            </p>
          </div>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="mb-6 grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          {
            label: "Total Scans",
            value: reports.length,
            icon: ScanSearch,
            color: "text-primary",
            bg: "bg-primary/10",
          },
          {
            label: "Approved",
            value: reports.filter((r) => r.overall_status === "APPROVED").length,
            icon: CheckCircle2,
            color: "text-emerald-400",
            bg: "bg-emerald-500/10",
          },
          {
            label: "Rejected",
            value: reports.filter((r) => r.overall_status === "REJECTED").length,
            icon: AlertTriangle,
            color: "text-rose-400",
            bg: "bg-rose-500/10",
          },
          {
            label: "Pending Review",
            value: reports.filter((r) => r.overall_status === "NEEDS_REVIEW")
              .length,
            icon: Activity,
            color: "text-amber-400",
            bg: "bg-amber-500/10",
          },
        ].map((stat) => (
          <div key={stat.label} className="glass-card rounded-xl p-4">
            <div className="flex items-center gap-3">
              <div
                className={`flex h-9 w-9 items-center justify-center rounded-lg ${stat.bg}`}
              >
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </div>
              <div>
                <p className="text-xl font-bold text-foreground">
                  {stat.value}
                </p>
                <p className="text-[10px] text-muted-foreground">
                  {stat.label}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Site Context Configuration */}
      <div className="mb-6 glass-card rounded-2xl p-5 animate-fade-in">
        <h2 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
          <Settings className="h-4 w-4 text-primary" />
          Site Configuration (Goa Municipal)
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="text-[10px] text-muted-foreground uppercase font-bold mb-1.5 block">
              Municipal Zone
            </label>
            <select
              value={siteContext.zone}
              onChange={(e) => setSiteContext({ ...siteContext, zone: e.target.value })}
              className="w-full bg-white/[0.05] border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary transition-all"
            >
              <option value="S1">S1 (Residential - Low Density)</option>
              <option value="S2">S2 (Residential - Med Density)</option>
              <option value="C1">C1 (Commercial)</option>
              <option value="I1">I1 (Industrial)</option>
              <option value="VP">VP (Village Panchayat)</option>
            </select>
          </div>
          <div>
            <label className="text-[10px] text-muted-foreground uppercase font-bold mb-1.5 block">
              Plot Area (sq.m)
            </label>
            <input
              type="number"
              value={siteContext.plot_area}
              onChange={(e) => setSiteContext({ ...siteContext, plot_area: Number(e.target.value) })}
              className="w-full bg-white/[0.05] border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary transition-all"
            />
          </div>
          <div>
            <label className="text-[10px] text-muted-foreground uppercase font-bold mb-1.5 block">
              Road Width (m)
            </label>
            <input
              type="number"
              value={siteContext.road_width}
              onChange={(e) => setSiteContext({ ...siteContext, road_width: Number(e.target.value) })}
              className="w-full bg-white/[0.05] border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary transition-all"
            />
          </div>
        </div>
      </div>

      {/* File Uploader */}
      <div className="mb-6">
        <FileUploader
          onFileSelected={handleFileSelected}
          stage={stage}
          progress={progress}
        />
      </div>

      {/* Processing Indicator */}
      {stage !== "idle" && stage !== "complete" && stage !== "error" && (
        <div className="mb-6">
          <ProcessingIndicator stage={stage} />
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-6 glass-card rounded-xl border-rose-500/30 bg-rose-500/[0.05] p-4">
          <p className="text-sm text-rose-400 font-medium">Error: {error}</p>
          <p className="text-xs text-muted-foreground mt-1">
            Make sure the backend server is running at{" "}
            <code className="text-xs bg-white/5 rounded px-1">
              http://localhost:8000
            </code>
          </p>
        </div>
      )}

      {/* Results */}
      {report && stage === "complete" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8 animate-fade-up">
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
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-primary" />
                Compliance Report
              </h2>
              <button 
                onClick={() => setStage("idle")}
                className="text-[10px] font-bold uppercase tracking-wider text-primary hover:underline"
              >
                New Analysis
              </button>
            </div>
            <ComplianceChecklist
              checks={report.compliance_checks}
              overallStatus={report.overall_status}
              summary={report.summary}
            />
          </div>
        </div>
      )}

      {/* Recent Reports */}
      {reports.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-foreground mb-3">
            Recent Reports
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {reports.slice(0, 6).map((r) => (
              <ReportCard key={r.report_id} report={r} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
