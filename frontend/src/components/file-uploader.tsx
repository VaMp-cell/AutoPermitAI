"use client";

import { useCallback, useState, useRef } from "react";
import { cn } from "@/lib/utils";
import { Upload, FileUp, X, FileText, Loader2 } from "lucide-react";
import type { PipelineStage } from "@/lib/types";

interface FileUploaderProps {
  onFileSelected: (file: File) => void;
  stage: PipelineStage;
  progress?: number;
}

export default function FileUploader({
  onFileSelected,
  stage,
  progress = 0,
}: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      if (stage === "idle") setIsDragging(true);
    },
    [stage]
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      if (stage !== "idle") return;

      const file = e.dataTransfer.files[0];
      if (file && file.type === "application/pdf") {
        setSelectedFile(file);
        onFileSelected(file);
      }
    },
    [stage, onFileSelected]
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        setSelectedFile(file);
        onFileSelected(file);
        // Reset value so the same file can be selected again if needed
        e.target.value = "";
      }
    },
    [onFileSelected]
  );

  const handleReset = useCallback(() => {
    setSelectedFile(null);
    if (inputRef.current) inputRef.current.value = "";
  }, []);

  const isProcessing = !["idle", "complete", "error"].includes(stage);

  return (
    <div className="w-full">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => {
          if (["idle", "complete", "error"].includes(stage)) {
            inputRef.current?.click();
          }
        }}
        className={cn(
          "glass-card relative cursor-pointer overflow-hidden rounded-2xl p-8 transition-all duration-300",
          isDragging && "border-primary/50 bg-primary/[0.06] scale-[1.01]",
          (stage === "idle" || stage === "complete" || stage === "error") && !isDragging && "hover:border-white/[0.15] hover:bg-white/[0.05]",
          isProcessing && "cursor-default",
          stage === "complete" && "border-emerald-500/30 bg-emerald-500/[0.05]",
          stage === "error" && "border-rose-500/30 bg-rose-500/[0.05]"
        )}
      >
        {/* Progress bar overlay */}
        {isProcessing && (
          <div className="absolute inset-x-0 bottom-0 h-1 bg-white/[0.05]">
            <div
              className="h-full bg-primary transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="hidden"
          id="blueprint-upload"
        />

        <div className="flex flex-col items-center gap-4 text-center">
          {/* Icon */}
          <div
            className={cn(
              "flex h-16 w-16 items-center justify-center rounded-2xl transition-all duration-300",
              stage === "idle"
                ? "bg-primary/15"
                : stage === "complete"
                ? "bg-emerald-500/15"
                : stage === "error"
                ? "bg-rose-500/15"
                : "bg-primary/15"
            )}
          >
            {isProcessing ? (
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            ) : stage === "complete" ? (
              <FileText className="h-8 w-8 text-emerald-400" />
            ) : (
              <Upload
                className={cn(
                  "h-8 w-8 transition-transform duration-300",
                  isDragging
                    ? "scale-110 text-primary"
                    : "text-muted-foreground"
                )}
              />
            )}
          </div>

          {/* Text */}
          {stage === "idle" && !selectedFile && (
            <>
              <div>
                <p className="text-sm font-semibold text-foreground">
                  Drop your blueprint PDF here
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  or click to browse • PDF files only
                </p>
              </div>
              <div className="flex items-center gap-2 rounded-lg bg-primary/10 px-4 py-2">
                <FileUp className="h-4 w-4 text-primary" />
                <span className="text-xs font-medium text-primary">
                  Select File
                </span>
              </div>
            </>
          )}

          {selectedFile && stage === "idle" && (
            <div className="flex items-center gap-3">
              <FileText className="h-5 w-5 text-primary" />
              <span className="text-sm font-medium">{selectedFile.name}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleReset();
                }}
                className="rounded-full p-1 hover:bg-white/10"
              >
                <X className="h-4 w-4 text-muted-foreground" />
              </button>
            </div>
          )}

          {isProcessing && (
            <p className="text-sm font-medium text-primary animate-pulse">
              Processing your blueprint...
            </p>
          )}

          {stage === "complete" && (
            <p className="text-sm font-medium text-emerald-400">
              ✓ Analysis complete — view your report below
            </p>
          )}

          {stage === "error" && (
            <div className="text-center">
              <p className="text-sm font-medium text-rose-400">
                Analysis failed
              </p>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleReset();
                }}
                className="mt-2 text-xs text-muted-foreground hover:text-foreground underline"
              >
                Try again
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
