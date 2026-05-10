"use client";

import { cn } from "@/lib/utils";
import type { PipelineStage } from "@/lib/types";
import {
  FileImage,
  ScanSearch,
  Type,
  BrainCircuit,
  CheckCircle2,
  Loader2,
} from "lucide-react";

interface ProcessingIndicatorProps {
  stage: PipelineStage;
}

const stages = [
  {
    key: "uploading" as PipelineStage,
    label: "Uploading PDF",
    description: "Transferring your blueprint to the server",
    icon: FileImage,
  },
  {
    key: "converting" as PipelineStage,
    label: "Converting Pages",
    description: "Rendering PDF pages to high-resolution images",
    icon: FileImage,
  },
  {
    key: "detecting" as PipelineStage,
    label: "Detecting Elements",
    description: "YOLOv8 scanning for structural elements",
    icon: ScanSearch,
  },
  {
    key: "ocr" as PipelineStage,
    label: "Reading Dimensions",
    description: "OCR extracting measurements and annotations",
    icon: Type,
  },
  {
    key: "analyzing" as PipelineStage,
    label: "Compliance Analysis",
    description: "AI evaluating building code compliance",
    icon: BrainCircuit,
  },
];

export default function ProcessingIndicator({
  stage,
}: ProcessingIndicatorProps) {
  if (stage === "idle" || stage === "complete" || stage === "error") {
    return null;
  }

  const currentIndex = stages.findIndex((s) => s.key === stage);

  return (
    <div className="glass-card rounded-2xl p-6 animate-fade-up">
      <div className="mb-5 flex items-center gap-2">
        <Loader2 className="h-4 w-4 animate-spin text-primary" />
        <h3 className="text-sm font-semibold text-foreground">
          Processing Blueprint
        </h3>
      </div>

      <div className="space-y-3">
        {stages.map((s, i) => {
          const isActive = i === currentIndex;
          const isComplete = i < currentIndex;
          const isPending = i > currentIndex;
          const Icon = isComplete ? CheckCircle2 : s.icon;

          return (
            <div
              key={s.key}
              className={cn(
                "flex items-center gap-4 rounded-xl px-4 py-3 transition-all duration-500",
                isActive && "bg-primary/[0.08] border border-primary/20",
                isComplete && "opacity-60",
                isPending && "opacity-30"
              )}
            >
              {/* Step indicator */}
              <div
                className={cn(
                  "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-all duration-300",
                  isActive && "bg-primary/20",
                  isComplete && "bg-emerald-500/20",
                  isPending && "bg-white/[0.05]"
                )}
              >
                {isActive ? (
                  <Loader2
                    className="h-4 w-4 animate-spin text-primary"
                  />
                ) : (
                  <Icon
                    className={cn(
                      "h-4 w-4",
                      isComplete
                        ? "text-emerald-400"
                        : "text-muted-foreground"
                    )}
                  />
                )}
              </div>

              {/* Label */}
              <div className="flex-1 min-w-0">
                <p
                  className={cn(
                    "text-sm font-medium",
                    isActive
                      ? "text-primary"
                      : isComplete
                      ? "text-emerald-400"
                      : "text-muted-foreground"
                  )}
                >
                  {s.label}
                  {isComplete && " ✓"}
                </p>
                {isActive && (
                  <p className="text-[10px] text-muted-foreground mt-0.5 animate-pulse">
                    {s.description}
                  </p>
                )}
              </div>

              {/* Connector line */}
              {i < stages.length - 1 && (
                <div
                  className={cn(
                    "absolute left-[2.15rem] mt-12 h-3 w-px",
                    isComplete ? "bg-emerald-500/40" : "bg-white/[0.08]"
                  )}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Progress fraction */}
      <div className="mt-4 text-center text-[10px] text-muted-foreground">
        Step {Math.min(currentIndex + 1, stages.length)} of {stages.length}
      </div>
    </div>
  );
}
