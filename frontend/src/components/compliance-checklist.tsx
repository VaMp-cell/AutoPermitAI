"use client";

import { useState } from "react";
import type { ComplianceCheck, OverallStatus } from "@/lib/types";
import { cn, getStatusColor } from "@/lib/utils";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
  ChevronDown,
  Shield,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";

interface ComplianceChecklistProps {
  checks: ComplianceCheck[];
  overallStatus: OverallStatus;
  summary: string;
}

const statusIcons = {
  PASS: CheckCircle2,
  FAIL: XCircle,
  WARNING: AlertTriangle,
  NOT_FOUND: HelpCircle,
};

const statusLabels = {
  PASS: "Passed",
  FAIL: "Failed",
  WARNING: "Warning",
  NOT_FOUND: "Not Found",
};

const overallStatusConfig: Record<
  OverallStatus,
  {
    icon: typeof ShieldCheck;
    label: string;
    color: string;
    bgColor: string;
    borderColor: string;
  }
> = {
  APPROVED: {
    icon: ShieldCheck,
    label: "Approved",
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/30",
  },
  REJECTED: {
    icon: ShieldAlert,
    label: "Rejected",
    color: "text-rose-400",
    bgColor: "bg-rose-500/10",
    borderColor: "border-rose-500/30",
  },
  NEEDS_REVIEW: {
    icon: Shield,
    label: "Needs Review",
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/30",
  },
};

export default function ComplianceChecklist({
  checks,
  overallStatus,
  summary,
}: ComplianceChecklistProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const config = overallStatusConfig[overallStatus];
  const OverallIcon = config.icon;

  const passCount = checks.filter((c) => c.status === "PASS").length;
  const failCount = checks.filter((c) => c.status === "FAIL").length;
  const warnCount = checks.filter(
    (c) => c.status === "WARNING" || c.status === "NOT_FOUND"
  ).length;

  return (
    <div className="flex flex-col gap-4">
      {/* Overall Status Banner */}
      <div
        className={cn(
          "glass-card rounded-xl p-4",
          config.bgColor,
          config.borderColor
        )}
      >
        <div className="flex items-center gap-3">
          <OverallIcon className={cn("h-8 w-8", config.color)} />
          <div className="flex-1">
            <h3 className={cn("text-lg font-bold", config.color)}>
              {config.label}
            </h3>
            <p className="mt-0.5 text-xs text-muted-foreground line-clamp-2">
              {summary}
            </p>
          </div>
        </div>

        {/* Stats bar */}
        <div className="mt-3 flex gap-3">
          <div className="flex items-center gap-1.5 text-xs">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
            <span className="text-emerald-400 font-semibold">{passCount}</span>
            <span className="text-muted-foreground">Passed</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs">
            <XCircle className="h-3.5 w-3.5 text-rose-400" />
            <span className="text-rose-400 font-semibold">{failCount}</span>
            <span className="text-muted-foreground">Failed</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs">
            <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
            <span className="text-amber-400 font-semibold">{warnCount}</span>
            <span className="text-muted-foreground">Warnings</span>
          </div>
        </div>
      </div>

      {/* Check Items */}
      <div className="space-y-2">
        {checks.map((check, i) => {
          const StatusIcon = statusIcons[check.status];
          const colors = getStatusColor(check.status);
          const isExpanded = expandedIndex === i;

          return (
            <div
              key={i}
              className={cn(
                "glass-card overflow-hidden rounded-xl transition-all duration-200",
                isExpanded && "ring-1 ring-white/10"
              )}
            >
              {/* Header */}
              <button
                onClick={() =>
                  setExpandedIndex(isExpanded ? null : i)
                }
                className="flex w-full items-center gap-3 p-3.5 text-left transition-colors hover:bg-white/[0.03]"
                id={`compliance-check-${i}`}
              >
                <StatusIcon
                  className={cn("h-5 w-5 shrink-0", colors.text)}
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">
                    {check.requirement}
                  </p>
                  <p className="text-[10px] text-muted-foreground mt-0.5">
                    {check.code_reference}
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span
                    className={cn(
                      "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold border",
                      colors.bg,
                      colors.text,
                      colors.border
                    )}
                  >
                    {statusLabels[check.status]}
                  </span>
                  <span
                    className={cn(
                      "text-[10px] px-1.5 py-0.5 rounded",
                      check.severity === "Critical"
                        ? "bg-rose-500/10 text-rose-400"
                        : check.severity === "Major"
                        ? "bg-amber-500/10 text-amber-400"
                        : "bg-blue-500/10 text-blue-400"
                    )}
                  >
                    {check.severity}
                  </span>
                  <ChevronDown
                    className={cn(
                      "h-4 w-4 text-muted-foreground transition-transform duration-200",
                      isExpanded && "rotate-180"
                    )}
                  />
                </div>
              </button>

              {/* Expanded detail */}
              {isExpanded && (
                <div className="border-t border-white/[0.05] bg-white/[0.02] p-4 animate-fade-up">
                  <div className="space-y-3 text-xs">
                    {/* Reasoning */}
                    <div>
                      <p className="font-semibold text-muted-foreground uppercase tracking-wider text-[10px] mb-1">
                        Analysis
                      </p>
                      <p className="text-foreground/80 leading-relaxed">
                        {check.reasoning}
                      </p>
                    </div>

                    {/* Values comparison */}
                    <div className="flex gap-4">
                      {check.detected_value && (
                        <div className="flex-1 rounded-lg bg-white/[0.03] p-2.5">
                          <p className="text-[10px] text-muted-foreground mb-0.5">
                            Detected
                          </p>
                          <p className="text-sm font-medium text-foreground">
                            {check.detected_value}
                          </p>
                        </div>
                      )}
                      {check.required_value && (
                        <div className="flex-1 rounded-lg bg-white/[0.03] p-2.5">
                          <p className="text-[10px] text-muted-foreground mb-0.5">
                            Required
                          </p>
                          <p className="text-sm font-medium text-foreground">
                            {check.required_value}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
