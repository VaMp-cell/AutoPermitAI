"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { listReports } from "@/lib/api";
import type { ReportListItem } from "@/lib/types";
import { 
  FileText, 
  ChevronRight, 
  Calendar, 
  CheckCircle2, 
  AlertTriangle, 
  Activity,
  ArrowLeft,
  ScanSearch
} from "lucide-react";

export default function ReportsListPage() {
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listReports()
      .then((data) => {
        setReports(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load reports");
        setLoading(false);
      });
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "APPROVED":
        return <CheckCircle2 className="h-4 w-4 text-emerald-400" />;
      case "REJECTED":
        return <AlertTriangle className="h-4 w-4 text-rose-400" />;
      default:
        return <Activity className="h-4 w-4 text-amber-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "APPROVED":
        return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
      case "REJECTED":
        return "text-rose-400 bg-rose-500/10 border-rose-500/20";
      default:
        return "text-amber-400 bg-amber-500/10 border-amber-500/20";
    }
  };

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto">
      <div className="mb-8 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <Link 
            href="/" 
            className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors mb-4"
          >
            <ArrowLeft className="h-3 w-3" />
            Back to Dashboard
          </Link>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/15">
              <FileText className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-foreground">
                Analysis History
              </h1>
              <p className="text-sm text-muted-foreground">
                View all previously generated compliance reports
              </p>
            </div>
          </div>
        </div>

        <Link 
          href="/" 
          className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary/90 transition-all shadow-lg shadow-primary/20"
        >
          <ScanSearch className="h-4 w-4" />
          New Analysis
        </Link>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 text-muted-foreground">
          <div className="h-8 w-8 border-2 border-primary/30 border-t-primary rounded-full animate-spin mb-4" />
          <p className="text-sm font-medium">Loading reports...</p>
        </div>
      ) : error ? (
        <div className="glass-card rounded-xl border-rose-500/30 bg-rose-500/[0.05] p-6 text-center">
          <AlertTriangle className="h-8 w-8 text-rose-500 mx-auto mb-3" />
          <p className="text-sm text-rose-400 font-medium">Failed to load reports</p>
          <p className="text-xs text-muted-foreground mt-1">{error}</p>
        </div>
      ) : reports.length === 0 ? (
        <div className="glass-card rounded-2xl p-12 text-center">
          <div className="h-16 w-16 bg-white/[0.02] border border-white/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <FileText className="h-8 w-8 text-muted-foreground/50" />
          </div>
          <h3 className="text-lg font-semibold text-foreground">No reports found</h3>
          <p className="text-sm text-muted-foreground mt-2 max-w-xs mx-auto">
            You haven't generated any compliance reports yet. Start by uploading a blueprint on the dashboard.
          </p>
          <Link 
            href="/" 
            className="inline-flex items-center gap-2 mt-6 bg-primary text-primary-foreground px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            Go to Dashboard
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {reports.map((report) => (
            <Link 
              key={report.report_id} 
              href={`/report/${report.report_id}`}
              className="group glass-card rounded-xl p-4 flex items-center gap-4 hover:bg-white/[0.05] transition-all"
            >
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-white/[0.03] border border-white/10">
                <FileText className="h-6 w-6 text-muted-foreground group-hover:text-primary transition-colors" />
              </div>
              
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold text-foreground truncate">
                  {report.filename}
                </h3>
                <div className="flex items-center gap-3 mt-1">
                  <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                    <Calendar className="h-3 w-3" />
                    {new Date(report.created_at).toLocaleDateString()}
                  </div>
                  <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[9px] font-bold uppercase tracking-wider ${getStatusColor(report.overall_status)}`}>
                    {getStatusIcon(report.overall_status)}
                    {report.overall_status.replace("_", " ")}
                  </div>
                </div>
              </div>

              <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:text-foreground group-hover:translate-x-0.5 transition-all" />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
