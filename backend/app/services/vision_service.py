"""
AutoPermit AI — Vision Service
Handles PDF-to-image conversion and YOLOv8 object detection on blueprints.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Tuple

import fitz  # PyMuPDF
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO

from app.schemas import DetectionBox

logger = logging.getLogger(__name__)

# ── Color palette for bounding box rendering ──────────────────────────────────
LABEL_COLORS = {
    "fire_exit": (239, 68, 68),      # Red
    "staircase": (59, 130, 246),     # Blue
    "parking": (34, 197, 94),        # Green
    "door": (249, 115, 22),          # Orange
    "window": (168, 85, 247),        # Purple
    "elevator": (236, 72, 153),      # Pink
    "ramp": (20, 184, 166),          # Teal
    "corridor": (245, 158, 11),      # Amber
    "room": (107, 114, 128),         # Gray
    "wall": (75, 85, 99),            # Dark Gray
}
DEFAULT_COLOR = (99, 102, 241)       # Indigo fallback


class VisionService:
    """Manages YOLOv8 model loading, PDF conversion, and inference."""

    def __init__(self, model_path: str = "yolov8n.pt"):
        """
        Initialize the vision service.

        Args:
            model_path: Path to the YOLOv8 .pt weight file.
        """
        self.model_path = model_path
        self.model: YOLO | None = None

    def load_model(self) -> None:
        """Load the YOLOv8 model into memory. Call once at startup."""
        logger.info(f"Loading YOLOv8 model from: {self.model_path}")
        self.model = YOLO(self.model_path)
        logger.info(f"Model loaded — {len(self.model.names)} classes available")

    # ── PDF Conversion ────────────────────────────────────────────────────────

    @staticmethod
    def pdf_to_images(pdf_path: str | Path, dpi: int = 300) -> List[Image.Image]:
        """
        Convert a PDF file to a list of PIL images (one per page).

        Args:
            pdf_path: Path to the PDF file.
            dpi: Resolution for rendering (default 300 for blueprint detail).

        Returns:
            List of PIL Image objects.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        images: List[Image.Image] = []
        doc = fitz.open(str(pdf_path))

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            # Scale matrix for target DPI (fitz default is 72 DPI)
            zoom = dpi / 72
            matrix = fitz.Matrix(zoom, zoom)
            pixmap = page.get_pixmap(matrix=matrix)

            img = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            images.append(img)
            logger.info(f"Converted page {page_num + 1}/{len(doc)} — {pixmap.width}x{pixmap.height}px")

        doc.close()
        return images

    # ── Object Detection ──────────────────────────────────────────────────────

    def detect_elements(
        self,
        image: Image.Image,
        confidence_threshold: float = 0.25,
    ) -> List[DetectionBox]:
        """
        Run YOLOv8 inference on a single image.

        Args:
            image: PIL Image to analyze.
            confidence_threshold: Minimum confidence to include a detection.

        Returns:
            List of DetectionBox with normalized coordinates (0-1).
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Convert PIL to numpy for YOLO
        img_array = np.array(image)
        results = self.model(img_array, conf=confidence_threshold, verbose=False)

        detections: List[DetectionBox] = []
        img_h, img_w = img_array.shape[:2]

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for i in range(len(boxes)):
                # Get box coordinates (xyxy format)
                x1, y1, x2, y2 = boxes.xyxy[i].tolist()
                conf = float(boxes.conf[i])
                cls_id = int(boxes.cls[i])
                label = self.model.names.get(cls_id, f"class_{cls_id}")

                # Normalize to 0-1 range
                cx = ((x1 + x2) / 2) / img_w
                cy = ((y1 + y2) / 2) / img_h
                w = (x2 - x1) / img_w
                h = (y2 - y1) / img_h

                detections.append(
                    DetectionBox(
                        label=label,
                        confidence=round(conf, 4),
                        x=round(cx, 6),
                        y=round(cy, 6),
                        width=round(w, 6),
                        height=round(h, 6),
                    )
                )

        logger.info(f"Detected {len(detections)} elements on image ({img_w}x{img_h})")
        return detections

    # ── Visualization ─────────────────────────────────────────────────────────

    @staticmethod
    def render_detections(
        image: Image.Image,
        detections: List[DetectionBox],
        line_width: int = 3,
    ) -> Image.Image:
        """
        Draw color-coded bounding boxes onto a copy of the blueprint image.

        Args:
            image: Original blueprint image.
            detections: List of detected elements.
            line_width: Thickness of bounding box lines.

        Returns:
            New PIL Image with bounding boxes drawn.
        """
        annotated = image.copy()
        draw = ImageDraw.Draw(annotated)
        img_w, img_h = annotated.size

        # Try to load a nicer font, fall back to default
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except (IOError, OSError):
            font = ImageFont.load_default()

        for det in detections:
            # Convert normalized coords back to pixel coords
            cx, cy = det.x * img_w, det.y * img_h
            bw, bh = det.width * img_w, det.height * img_h
            x1 = cx - bw / 2
            y1 = cy - bh / 2
            x2 = cx + bw / 2
            y2 = cy + bh / 2

            color = LABEL_COLORS.get(det.label, DEFAULT_COLOR)
            label_text = f"{det.label} {det.confidence:.0%}"

            # Draw bounding box
            draw.rectangle([x1, y1, x2, y2], outline=color, width=line_width)

            # Draw label background
            text_bbox = draw.textbbox((x1, y1 - 20), label_text, font=font)
            draw.rectangle(
                [text_bbox[0] - 2, text_bbox[1] - 2, text_bbox[2] + 2, text_bbox[3] + 2],
                fill=color,
            )
            draw.text((x1, y1 - 20), label_text, fill=(255, 255, 255), font=font)

        return annotated

    # ── Convenience ───────────────────────────────────────────────────────────

    def process_blueprint(
        self,
        pdf_path: str | Path,
        output_dir: str | Path,
        page_index: int = 0,
    ) -> Tuple[Image.Image, Image.Image, List[DetectionBox]]:
        """
        Full pipeline: PDF → Image → Detect → Render.

        Args:
            pdf_path: Path to the uploaded PDF.
            output_dir: Directory to save processed images.
            page_index: Which page to process (default: first page).

        Returns:
            Tuple of (original_image, annotated_image, detections).
        """
        images = self.pdf_to_images(pdf_path)
        if page_index >= len(images):
            raise ValueError(f"Page {page_index} does not exist (PDF has {len(images)} pages)")

        image = images[page_index]
        detections = self.detect_elements(image)
        annotated = self.render_detections(image, detections)

        # Save images
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        original_path = output_dir / "original.jpg"
        annotated_path = output_dir / "annotated.jpg"
        image.save(str(original_path), quality=95)
        annotated.save(str(annotated_path), quality=95)

        logger.info(f"Saved images to {output_dir}")
        return image, annotated, detections
