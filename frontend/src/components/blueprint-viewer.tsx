"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import type { DetectionBox } from "@/lib/types";
import { cn, formatConfidence } from "@/lib/utils";
import { ZoomIn, ZoomOut, RotateCcw } from "lucide-react";

/** Color palette for detection labels */
const LABEL_COLORS: Record<string, string> = {
  fire_exit: "#ef4444",
  staircase: "#3b82f6",
  parking: "#22c55e",
  door: "#f97316",
  window: "#a855f7",
  elevator: "#ec4899",
  ramp: "#14b8a6",
  corridor: "#f59e0b",
  room: "#6b7280",
  wall: "#4b5563",
  person: "#06b6d4",
  car: "#10b981",
  chair: "#8b5cf6",
  table: "#d946ef",
};
const DEFAULT_COLOR = "#6366f1";

interface BlueprintViewerProps {
  imageUrl: string;
  detections: DetectionBox[];
  className?: string;
}

export default function BlueprintViewer({
  imageUrl,
  detections,
  className,
}: BlueprintViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [scale, setScale] = useState(1);
  const [hoveredBox, setHoveredBox] = useState<number | null>(null);
  const [tooltip, setTooltip] = useState<{
    x: number;
    y: number;
    detection: DetectionBox;
  } | null>(null);

  // Load image
  useEffect(() => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => setImage(img);
    img.onerror = () => console.error("Failed to load blueprint image");
    img.src = imageUrl;
  }, [imageUrl]);

  // Draw canvas
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx || !image) return;

    const container = containerRef.current;
    if (!container) return;

    // Size canvas to container
    const rect = container.getBoundingClientRect();
    const displayWidth = rect.width;
    const aspectRatio = image.height / image.width;
    const displayHeight = displayWidth * aspectRatio;

    canvas.width = displayWidth * window.devicePixelRatio;
    canvas.height = displayHeight * window.devicePixelRatio;
    canvas.style.width = `${displayWidth}px`;
    canvas.style.height = `${displayHeight}px`;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    // Clear and draw image
    ctx.clearRect(0, 0, displayWidth, displayHeight);
    ctx.save();
    ctx.scale(scale, scale);

    const imgW = displayWidth / scale;
    const imgH = displayHeight / scale;
    ctx.drawImage(image, 0, 0, imgW, imgH);

    // Draw bounding boxes
    detections.forEach((det, i) => {
      const color = LABEL_COLORS[det.label] || DEFAULT_COLOR;
      const isHovered = hoveredBox === i;

      // Convert normalized coords to pixel coords
      const cx = det.x * imgW;
      const cy = det.y * imgH;
      const bw = det.width * imgW;
      const bh = det.height * imgH;
      const x1 = cx - bw / 2;
      const y1 = cy - bh / 2;

      // Box
      ctx.strokeStyle = color;
      ctx.lineWidth = isHovered ? 3 : 2;
      ctx.strokeRect(x1, y1, bw, bh);

      // Semi-transparent fill on hover
      if (isHovered) {
        ctx.fillStyle = color + "20";
        ctx.fillRect(x1, y1, bw, bh);
      }

      // Label background
      const label = `${det.label} ${formatConfidence(det.confidence)}`;
      ctx.font = `${isHovered ? "bold " : ""}11px Inter, system-ui, sans-serif`;
      const textMetrics = ctx.measureText(label);
      const textH = 18;
      const textW = textMetrics.width + 10;
      const labelY = Math.max(y1 - textH - 2, 0);

      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.roundRect(x1, labelY, textW, textH, 3);
      ctx.fill();

      ctx.fillStyle = "#ffffff";
      ctx.fillText(label, x1 + 5, labelY + 13);
    });

    ctx.restore();
  }, [image, detections, scale, hoveredBox]);

  useEffect(() => {
    draw();
  }, [draw]);

  // Resize observer
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver(() => draw());
    observer.observe(container);
    return () => observer.disconnect();
  }, [draw]);

  // Mouse hover for tooltips
  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const canvas = canvasRef.current;
      if (!canvas || !image) return;

      const rect = canvas.getBoundingClientRect();
      const mx = (e.clientX - rect.left) / scale;
      const my = (e.clientY - rect.top) / scale;
      const imgW = rect.width / scale;
      const imgH = rect.height / scale;

      let found = false;
      detections.forEach((det, i) => {
        const cx = det.x * imgW;
        const cy = det.y * imgH;
        const bw = det.width * imgW;
        const bh = det.height * imgH;
        const x1 = cx - bw / 2;
        const y1 = cy - bh / 2;

        if (mx >= x1 && mx <= x1 + bw && my >= y1 && my <= y1 + bh) {
          setHoveredBox(i);
          setTooltip({
            x: e.clientX - rect.left,
            y: e.clientY - rect.top,
            detection: det,
          });
          found = true;
        }
      });

      if (!found) {
        setHoveredBox(null);
        setTooltip(null);
      }
    },
    [image, detections, scale]
  );

  return (
    <div className={cn("relative", className)}>
      {/* Controls */}
      <div className="absolute right-3 top-3 z-10 flex gap-1.5">
        {[
          {
            icon: ZoomIn,
            action: () => setScale((s) => Math.min(s + 0.25, 3)),
            label: "Zoom in",
          },
          {
            icon: ZoomOut,
            action: () => setScale((s) => Math.max(s - 0.25, 0.5)),
            label: "Zoom out",
          },
          {
            icon: RotateCcw,
            action: () => setScale(1),
            label: "Reset zoom",
          },
        ].map(({ icon: Icon, action, label }) => (
          <button
            key={label}
            onClick={action}
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-background/80 backdrop-blur-sm border border-white/10 text-muted-foreground hover:text-foreground hover:bg-background transition-all"
            aria-label={label}
          >
            <Icon className="h-4 w-4" />
          </button>
        ))}
      </div>

      {/* Scale indicator */}
      <div className="absolute left-3 top-3 z-10 rounded-md bg-background/80 backdrop-blur-sm border border-white/10 px-2 py-1 text-xs text-muted-foreground">
        {Math.round(scale * 100)}%
      </div>

      {/* Canvas container */}
      <div
        ref={containerRef}
        className="overflow-auto rounded-xl border border-white/[0.08] bg-black/20"
        style={{ maxHeight: "600px" }}
      >
        <canvas
          ref={canvasRef}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => {
            setHoveredBox(null);
            setTooltip(null);
          }}
          className="cursor-crosshair"
        />
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div
          className="pointer-events-none absolute z-20 rounded-lg bg-card/95 backdrop-blur-xl border border-white/10 p-3 shadow-xl"
          style={{
            left: tooltip.x + 12,
            top: tooltip.y - 10,
            maxWidth: "220px",
          }}
        >
          <p className="text-xs font-bold text-foreground capitalize">
            {tooltip.detection.label}
          </p>
          <p className="text-[10px] text-muted-foreground mt-1">
            Confidence: {formatConfidence(tooltip.detection.confidence)}
          </p>
          <p className="text-[10px] text-muted-foreground">
            Position: ({(tooltip.detection.x * 100).toFixed(1)}%,{" "}
            {(tooltip.detection.y * 100).toFixed(1)}%)
          </p>
        </div>
      )}

      {/* Detection count */}
      <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
        <span>{detections.length} elements detected</span>
        <div className="flex gap-2">
          {Object.entries(
            detections.reduce<Record<string, number>>((acc, d) => {
              acc[d.label] = (acc[d.label] || 0) + 1;
              return acc;
            }, {})
          )
            .slice(0, 5)
            .map(([label, count]) => (
              <span
                key={label}
                className="flex items-center gap-1.5 rounded-full bg-white/[0.05] px-2 py-0.5"
              >
                <span
                  className="h-2 w-2 rounded-full"
                  style={{
                    backgroundColor: LABEL_COLORS[label] || DEFAULT_COLOR,
                  }}
                />
                {label}: {count}
              </span>
            ))}
        </div>
      </div>
    </div>
  );
}
