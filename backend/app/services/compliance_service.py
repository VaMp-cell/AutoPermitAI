"""
AutoPermit AI — Compliance Service
Uses GPT-4o or Gemini 1.5 Flash to evaluate blueprint compliance against building codes.
"""

import json
import logging
import os
import re
from typing import List, Dict, Any, Optional

from app.config import settings
from app.prompts.municipal_logic import (
    MUNICIPAL_INSPECTOR_SYSTEM_PROMPT,
    build_analysis_prompt,
)
from app.schemas import ComplianceCheck, DetectionBox, OCRExtraction

logger = logging.getLogger(__name__)

class ComplianceService:
    """Orchestrates LLM-based building code compliance analysis."""

    def __init__(self):
        self.openai_client = None
        self.gemini_model = None
        self.provider = "MOCK"

    def initialize(self) -> None:
        """Initialize the selected AI provider."""
        # Try Gemini first (for free tier support)
        if settings.GOOGLE_API_KEY:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
                # Use full model resource names as seen in your logs
                self.gemini_candidates = [
                    'models/gemini-2.0-flash', 
                    'models/gemini-1.5-flash', 
                    'models/gemini-flash-latest'
                ]
                self.provider = "GEMINI"
                logger.info("✓ Gemini initialized (Multi-model support enabled)")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")

        # Fallback to OpenAI
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "sk-your-key-here":
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                self.provider = "OPENAI"
                logger.info("✓ OpenAI GPT-4o initialized")
                return
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")

        self.provider = "MOCK"
        logger.warning("No valid AI keys found. Running in MOCK mode.")

    def analyze(self, detections: list, ocr_results: list, image_path: str = "", extra_context: str = "") -> dict:
        """Orchestrate the compliance analysis using the best available AI provider."""
        user_prompt = build_analysis_prompt(
            str(detections), 
            str(ocr_results),
            extra_context
        )

        if self.provider == "GEMINI":
            return self._analyze_gemini(user_prompt, image_path)
        elif self.provider == "OPENAI":
            return self._analyze_openai(user_prompt)
        else:
            return self._mock_analysis(detections, ocr_results)

    def _analyze_gemini(self, user_prompt: str, image_path: str = "") -> dict:
        """Call Google Gemini with fallback and image support."""
        last_error = ""
        
        # Prepare content (image + text)
        contents = [user_prompt]
        if image_path and os.path.exists(image_path):
            try:
                from PIL import Image
                img = Image.open(image_path)
                contents.append(img)
                logger.info(f"Attached image {image_path} to Gemini request")
            except Exception as e:
                logger.warning(f"Failed to attach image to Gemini: {e}")

        for model_id in self.gemini_candidates:
            try:
                logger.info(f"Sending request to Gemini ({model_id})...")
                response = self.gemini_client.models.generate_content(
                    model=model_id,
                    contents=contents,
                    config={
                        'system_instruction': MUNICIPAL_INSPECTOR_SYSTEM_PROMPT,
                        'response_mime_type': 'application/json',
                    }
                )
                
                text = response.text
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                
                return json.loads(text)
            except Exception as e:
                logger.warning(f"Gemini {model_id} failed: {e}")
                last_error = str(e)
                continue
        
        logger.error(f"All Gemini candidates failed. Last error: {last_error}")
        return self._mock_analysis([], [], error=last_error)

    def _analyze_openai(self, user_prompt: str) -> dict:
        """Call OpenAI GPT-4o."""
        try:
            logger.info("Sending request to OpenAI GPT-4o...")
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": MUNICIPAL_INSPECTOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._mock_analysis([], [], error=str(e))

    def _format_detections(self, detections: List[DetectionBox]) -> str:
        if not detections: return "No structural elements detected."
        lines = []
        for det in detections:
            lines.append(f"- {det.label}: pos=({det.x:.2f},{det.y:.2f}) conf={det.confidence:.0%}")
        return "\n".join(lines)

    def _format_ocr(self, ocr_results: List[OCRExtraction]) -> str:
        if not ocr_results: return "No text found."
        lines = []
        for r in ocr_results:
            if r.value is not None:
                lines.append(f"- \"{r.text}\" -> {r.value}{r.unit or ''}")
        return "\n".join(lines)

    def _mock_analysis(self, detections: List[DetectionBox], ocr_results: List[OCRExtraction], error: str = None) -> dict:
        """Enhanced mock that uses actual OCR values if available."""
        # Find bedroom/kitchen sizes in OCR for a better 'fake' experience
        bed_area = 10.5
        for o in ocr_results:
            if "bed" in o.text.lower() and o.value: bed_area = o.value

        summary = "MOCK ANALYSIS: " + (error if error else "No API key found. Using template based on Goa 2010 rules.")
        
        return {
            "overall_status": "NEEDS_REVIEW",
            "summary": summary,
            "compliance_checks": [
                {
                    "code_reference": "MOCK_CHECK",
                    "requirement": "Blueprint must be analyzed by AI",
                    "status": "WARNING",
                    "severity": "Minor",
                    "reasoning": "This is a placeholder report. The real-time AI was unable to process this request. Check your API keys.",
                    "detected_value": "N/A",
                    "required_value": "AI Analysis"
                }
            ]
        }

    def parse_compliance_checks(self, raw_result: dict) -> List[ComplianceCheck]:
        checks = []
        for item in raw_result.get("compliance_checks", []):
            try:
                checks.append(ComplianceCheck(**item))
            except Exception: continue
        return checks
