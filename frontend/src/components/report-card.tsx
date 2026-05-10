"use client";

import Link from "next/link";
import type { ReportListItem } from "@/lib/types";
import { cn, formatDate, getStatusColor } from "@/lib/utils";
import {
  FileText,
  ChevronRight,
  ScanSearch,
  CheckCircle2,
} from "lucide-react";

interface ReportCardProps {
  report: ReportListItem;
}

export default function ReportCard({ report }: ReportCardProps) {
  const statusColors = getStatusColor(report.overall_status);

  return (
    <Link href={`/report/${report.report_id}`}>
      <div className="glass-card-hover group rounded-xl p-4 cursor-pointer">
        <div className="flex items-start gap-3">
          {/* Icon */}
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
            <FileText className="h-5 w-5 text-primary" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <p className="text-sm font-semibold text-foreground truncate">
                {report.filename}
              </p>
              <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <p className="text-[10px] text-muted-foreground mt-0.5">
              {formatDate(report.created_at)}
            </p>

            {/* Stats */}
            <div className="mt-2.5 flex items-center gap-3">
              <span
                className={cn(
                  "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold border",
                  statusColors.bg,
                  statusColors.text,
                  statusColors.border
                )}
              >
                {report.overall_status === "APPROVED"
                  ? "Approved"
                  : report.overall_status === "REJECTED"
                  ? "Rejected"
                  : "Needs Review"}
              </span>

              <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                <ScanSearch className="h-3 w-3" />
                {report.detection_count} detections
              </span>

              <span className="flex items-center gap-1 text-[10px] text-muted-foreground">
                <CheckCircle2 className="h-3 w-3" />
                {report.check_count} checks
              </span>
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
}
