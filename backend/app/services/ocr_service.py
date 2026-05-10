"""
AutoPermit AI — OCR Service
Extracts text and numeric dimensions from blueprint images using Tesseract OCR.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

from PIL import Image

from app.schemas import OCRExtraction

logger = logging.getLogger(__name__)


class OCRService:
    """Extracts text and dimensions from blueprint images using pytesseract."""

    def __init__(self):
        """Initialize OCR service."""
        self._available = False
        try:
            import pytesseract
            self._pytesseract = pytesseract
            self._available = True
            logger.info("pytesseract OCR initialized")
        except ImportError:
            logger.warning(
                "pytesseract not installed. OCR features will return empty results. "
                "Install with: pip install pytesseract (also install Tesseract-OCR binary)"
            )

    def extract_dimensions(self, image: Image.Image) -> List[OCRExtraction]:
        """
        Run OCR on a blueprint image and extract dimension annotations.

        Args:
            image: PIL Image of the blueprint.

        Returns:
            List of OCRExtraction objects with parsed measurements.
        """
        if not self._available:
            return []

        try:
            # Get detailed OCR data with bounding boxes
            data = self._pytesseract.image_to_data(
                image, output_type=self._pytesseract.Output.DICT
            )
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return []

        extractions: List[OCRExtraction] = []
        n_boxes = len(data["text"])

        for i in range(n_boxes):
            text = data["text"][i].strip()
            conf = int(data["conf"][i])

            # Skip empty or low-confidence results
            if not text or conf < 30:
                continue

            location = {
                "x1": data["left"][i],
                "y1": data["top"][i],
                "x2": data["left"][i] + data["width"][i],
                "y2": data["top"][i] + data["height"][i],
                "confidence": conf / 100.0,
            }

            # Try to parse as a measurement
            value, unit = self._parse_measurement(text)

            extractions.append(
                OCRExtraction(
                    text=text,
                    value=value,
                    unit=unit,
                    location=location,
                )
            )

        dimension_extractions = [e for e in extractions if e.value is not None]
        logger.info(
            f"OCR extracted {len(extractions)} text regions, "
            f"{len(dimension_extractions)} contain dimensions"
        )

        return extractions

    @staticmethod
    def _parse_measurement(text: str) -> Tuple[Optional[float], Optional[str]]:
        """
        Attempt to parse a text string as an architectural measurement.

        Args:
            text: Raw OCR text.

        Returns:
            Tuple of (numeric_value, unit) or (None, None) if not a measurement.
        """
        text = text.strip()

        # Feet and inches: 12'-6"
        ft_in_match = re.match(r"(\d+)['']\s*[-]?\s*(\d+)[\"\"]", text)
        if ft_in_match:
            feet = float(ft_in_match.group(1))
            inches = float(ft_in_match.group(2))
            total_inches = feet * 12 + inches
            return total_inches, "in"

        # Metric: 3.5m, 3500mm
        metric_match = re.match(r"(\d+\.?\d*)\s*(mm|cm|m|meter|meters)\b", text, re.IGNORECASE)
        if metric_match:
            value = float(metric_match.group(1))
            unit = metric_match.group(2).lower()
            if unit in ("meter", "meters"):
                unit = "m"
            return value, unit

        # Feet only: 25', 25 ft
        ft_match = re.match(r"(\d+\.?\d*)\s*(?:['']\s*$|(?:ft|feet)\b)", text, re.IGNORECASE)
        if ft_match:
            return float(ft_match.group(1)), "ft"

        # Inches only: 32", 32 in
        in_match = re.match(
            r"(\d+\.?\d*)\s*(?:[\"\"]|(?:in|inch|inches)\b)", text, re.IGNORECASE
        )
        if in_match:
            return float(in_match.group(1)), "in"

        # Plain number (context-dependent)
        plain_match = re.match(r"^(\d+\.?\d*)$", text)
        if plain_match:
            return float(plain_match.group(1)), None

        return None, None

    def format_for_llm(self, extractions: List[OCRExtraction]) -> str:
        """
        Format OCR extractions into a readable string for the LLM prompt.

        Args:
            extractions: List of OCR extraction results.

        Returns:
            Formatted string summarizing extracted dimensions.
        """
        if not extractions:
            return "No dimension annotations were found."

        lines = []
        for i, ext in enumerate(extractions, 1):
            if ext.value is not None:
                unit_str = f" {ext.unit}" if ext.unit else ""
                lines.append(f'  {i}. "{ext.text}" → {ext.value}{unit_str}')
            else:
                lines.append(f'  {i}. "{ext.text}" (non-numeric annotation)')

        return "\n".join(lines)
