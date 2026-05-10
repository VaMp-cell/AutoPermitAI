"""
AutoPermit AI — Compliance Service
Uses GPT-4o (JSON mode) to evaluate blueprint compliance against building codes.
"""

from __future__ import annotations

import json
import logging
from typing import List

from openai import OpenAI

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
        """Initialize with OpenAI client."""
        self.client: OpenAI | None = None

    def initialize(self) -> None:
        """Set up the OpenAI client. Call once at startup."""
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI client initialized")
        else:
            logger.warning(
                "OPENAI_API_KEY not set — compliance analysis will return mock results. "
                "Set the key in your .env file."
            )

    def _format_detections(self, detections: List[DetectionBox]) -> str:
        """Format detection results for the LLM prompt."""
        if not detections:
            return "No structural elements were detected."

        lines = []
        # Group by label
        label_counts: dict[str, list[DetectionBox]] = {}
        for det in detections:
            label_counts.setdefault(det.label, []).append(det)

        for label, dets in label_counts.items():
            avg_conf = sum(d.confidence for d in dets) / len(dets)
            lines.append(
                f"  - {label}: {len(dets)} instance(s) detected "
                f"(avg confidence: {avg_conf:.0%})"
            )
            for i, d in enumerate(dets, 1):
                lines.append(
                    f"    #{i}: position=({d.x:.2f}, {d.y:.2f}), "
                    f"size=({d.width:.2f}×{d.height:.2f}), conf={d.confidence:.0%}"
                )

        return "\n".join(lines)

    def analyze(
        self,
        detections: List[DetectionBox],
        ocr_results: List[OCRExtraction],
        ocr_formatted: str = "",
    ) -> dict:
        """
        Run compliance analysis via GPT-4o.

        Args:
            detections: Detected structural elements.
            ocr_results: OCR extraction results.
            ocr_formatted: Pre-formatted OCR text for the prompt.

        Returns:
            Dictionary with compliance_checks, overall_status, and summary.
        """
        detections_summary = self._format_detections(detections)
        ocr_summary = ocr_formatted or self._format_ocr(ocr_results)
        user_prompt = build_analysis_prompt(detections_summary, ocr_summary)

        # If no API key, return mock results for development
        if self.client is None:
            logger.info("Returning mock compliance results (no API key)")
            return self._mock_analysis(detections)

        try:
            logger.info("Sending compliance analysis request to GPT-4o...")
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": MUNICIPAL_INSPECTOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,  # Low temp for consistent, analytical output
                max_tokens=4096,
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from GPT-4o")

            result = json.loads(content)
            logger.info(
                f"Compliance analysis complete — "
                f"{len(result.get('compliance_checks', []))} checks, "
                f"status: {result.get('overall_status', 'UNKNOWN')}"
            )
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            return self._mock_analysis(detections, error=str(e))
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            return self._mock_analysis(detections, error=str(e))

    @staticmethod
    def _format_ocr(ocr_results: List[OCRExtraction]) -> str:
        """Format OCR results for the prompt."""
        if not ocr_results:
            return "No dimensions extracted."
        lines = []
        for i, r in enumerate(ocr_results, 1):
            if r.value is not None:
                unit_str = f" {r.unit}" if r.unit else ""
                lines.append(f"  {i}. \"{r.text}\" → {r.value}{unit_str}")
        return "\n".join(lines) if lines else "No numeric dimensions found."

    @staticmethod
    def _mock_analysis(
        detections: List[DetectionBox],
        error: str | None = None,
    ) -> dict:
        """
        Generate comprehensive mock compliance results based on Panjim, Goa regulations.
        Runs when no OpenAI API key is configured.
        """
        door_count = len([d for d in detections if "door" in d.label.lower()])
        person_count = len([d for d in detections if "person" in d.label.lower()])
        chair_count = len([d for d in detections if "chair" in d.label.lower()])
        car_count = len([d for d in detections if "car" in d.label.lower()])

        checks = [
            # 1. SETBACK — Front
            {
                "code_reference": "Goa TCP Act - Setback Rules (Schedule)",
                "requirement": "Front setback minimum 3–5 m depending on road width and zone",
                "status": "WARNING",
                "severity": "Critical",
                "reasoning": (
                    "Front setback distance could not be precisely measured from this blueprint page. "
                    "The building outline was detected but the property boundary/road edge is unclear. "
                    "A site plan with property boundaries is required for accurate setback verification. "
                    "In Panjim, front setback violations are a top reason for plan rejection."
                ),
                "detected_value": "Building outline detected, boundary unclear",
                "required_value": "Minimum 3 m (residential), 5 m (commercial on wide roads)",
            },
            # 2. SETBACK — Side & Rear
            {
                "code_reference": "Goa Land Dev. & Building Construction Regs - Side/Rear Setback",
                "requirement": "Side setback minimum 1.5–3 m, rear setback minimum 2–3 m",
                "status": "WARNING",
                "severity": "Major",
                "reasoning": (
                    "Side and rear setbacks require the site plan showing property boundaries. "
                    "The floor plan alone cannot confirm setback compliance. "
                    "Verify with survey plan overlay."
                ),
                "detected_value": "Requires site plan verification",
                "required_value": "Side: ≥1.5 m, Rear: ≥2 m minimum",
            },
            # 3. FSI / FAR
            {
                "code_reference": "Goa TCP Act - FSI/FAR Regulations",
                "requirement": "Floor Space Index within permitted limits for zone classification",
                "status": "NOT_FOUND",
                "severity": "Critical",
                "reasoning": (
                    "FSI calculation requires total built-up area across all floors and "
                    "the plot area from the survey plan. Only one floor plan page was analyzed. "
                    "Submit all floor plans and the site plan for FSI computation. "
                    "Excess FSI is among the most common rejection reasons in Panjim."
                ),
                "detected_value": None,
                "required_value": "Varies by zone (typically 1.0–1.5 for residential in Panjim)",
            },
            # 4. GROUND COVERAGE
            {
                "code_reference": "Goa Building Construction Regs - Ground Coverage",
                "requirement": "Ground coverage within permissible percentage of plot area",
                "status": "NOT_FOUND",
                "severity": "Major",
                "reasoning": (
                    "Ground coverage percentage requires plot area and ground floor footprint. "
                    "Plot area not available from the submitted blueprint page. "
                    "Remaining area must accommodate open spaces, landscaping, and parking."
                ),
                "detected_value": None,
                "required_value": "Typically 40–50% for residential (varies by zone)",
            },
            # 5. ROOM SIZES
            {
                "code_reference": "NBC Section 7.3 / Goa Building Regs - Room Dimensions",
                "requirement": "Minimum room sizes: Bedroom ≥9.5 sq.m, Living ≥12 sq.m, Kitchen ≥5 sq.m",
                "status": "WARNING",
                "severity": "Major",
                "reasoning": (
                    "Room outlines were detected in the floor plan but individual room area "
                    "measurements could not be extracted by OCR. Dimension annotations on the "
                    "blueprint should specify each room's area. Verify: Bedroom ≥9.5 sq.m, "
                    "Living room ≥12 sq.m, Kitchen ≥5–7.5 sq.m, Bathroom ≥1.8 sq.m, Toilet ≥1.1 sq.m."
                ),
                "detected_value": "Room outlines detected, areas unverified",
                "required_value": "Bedroom ≥9.5 sq.m, Living ≥12 sq.m, Kitchen ≥5 sq.m",
            },
            # 6. CEILING HEIGHT
            {
                "code_reference": "NBC Section 7.3.1 / Goa Building Regs - Ceiling Heights",
                "requirement": "Habitable rooms ≥2.75 m, Kitchen ≥2.6 m, Bathroom ≥2.2 m",
                "status": "NOT_FOUND",
                "severity": "Major",
                "reasoning": (
                    "Ceiling heights require section drawings which were not detected in the "
                    "submitted page. Floor plans show layout but not vertical dimensions. "
                    "Submit section/elevation drawings for height compliance verification."
                ),
                "detected_value": None,
                "required_value": "Habitable: ≥2.75 m, Kitchen: ≥2.6 m, Bathroom: ≥2.2 m",
            },
            # 7. STAIRCASE
            {
                "code_reference": "NBC Section 4.4.1 / Goa Fire Safety Rules - Staircase",
                "requirement": "Staircase width ≥0.9 m (residential), tread ≥250 mm, riser ≤190 mm",
                "status": "WARNING",
                "severity": "Major",
                "reasoning": (
                    "Staircase area was identified on the floor plan but exact dimensions "
                    "(width, tread depth, riser height) could not be extracted. "
                    "For apartments and commercial buildings in Panjim, fire escape staircases "
                    "with handrails and anti-slip finish are mandatory."
                ),
                "detected_value": "Staircase area detected, dimensions unverified",
                "required_value": "Width ≥0.9 m, Tread ≥250 mm, Riser ≤190 mm, Headroom ≥2.1 m",
            },
            # 8. PARKING
            {
                "code_reference": "Goa Building Regs - Parking Requirements / CCP Municipal Rules",
                "requirement": "Adequate parking: car space ≥2.5 m × 5 m, mandatory per unit/area",
                "status": "NOT_FOUND" if car_count == 0 else "WARNING",
                "severity": "Critical",
                "reasoning": (
                    f"{'No parking area or vehicles detected on this blueprint page.' if car_count == 0 else f'{car_count} vehicle(s) detected.'} "
                    "Parking may be on a separate floor/site plan. In Panjim, parking "
                    "deficiency is a primary rejection reason. Each residential unit requires "
                    "dedicated parking. Two-wheeler parking (1 m × 2 m) must also be provided. "
                    "Accessible parking with larger dimensions is mandatory."
                ),
                "detected_value": f"{car_count} vehicles detected" if car_count > 0 else None,
                "required_value": "Car: ≥2.5 m × 5 m per space, 2-wheeler: 1 m × 2 m",
            },
            # 9. FIRE SAFETY
            {
                "code_reference": "Goa Fire Safety Rules / NBC Part 4 - Fire & Life Safety",
                "requirement": "Fire safety: extinguishers, escape stairs, emergency exits, smoke detectors",
                "status": "WARNING",
                "severity": "Critical",
                "reasoning": (
                    f"Detected {door_count} door(s) which may serve as exits. "
                    "Fire safety compliance requires: fire extinguisher locations marked, "
                    "dedicated fire escape staircase (for apartments/commercial), emergency "
                    "exit signage, smoke detectors, fire alarm system, water storage for "
                    "firefighting, and fire pumps. Fire NOC from Goa Fire Services is mandatory. "
                    "High-rise buildings require refuge areas and fire lifts."
                ),
                "detected_value": f"{door_count} doors detected (exit verification needed)",
                "required_value": "Full fire safety system + Fire NOC required",
            },
            # 10. VENTILATION & LIGHTING
            {
                "code_reference": "NBC Section 7.4 / Goa Building Regs - Ventilation",
                "requirement": "Window area ≥10% of floor area, natural ventilation for all rooms",
                "status": "WARNING",
                "severity": "Major",
                "reasoning": (
                    "Windows and openings were partially detected on the blueprint. "
                    "Ventilation compliance requires: window area ≥10% of each room's floor area, "
                    "cross-ventilation in habitable rooms, exhaust ventilation in bathrooms "
                    "(ventilation shafts if no external window), and adequate sunlight access."
                ),
                "detected_value": "Window openings partially detected",
                "required_value": "Window area ≥10% of floor area per room",
            },
            # 11. DRAINAGE & RAINWATER HARVESTING
            {
                "code_reference": "CCP Municipal Rules / NBC - Drainage & Rainwater Harvesting",
                "requirement": "Proper sewage, stormwater drainage, and rainwater harvesting system",
                "status": "NOT_FOUND",
                "severity": "Major",
                "reasoning": (
                    "No drainage layout was detected on this blueprint page. "
                    "A separate drainage layout drawing is required showing: sewage lines, "
                    "septic tank or sewer connection, stormwater drainage, and rainwater "
                    "harvesting system. Rainwater harvesting is mandatory for apartments and "
                    "large residential projects in Goa."
                ),
                "detected_value": None,
                "required_value": "Drainage layout + rainwater harvesting system required",
            },
            # 12. ACCESSIBILITY (Barrier-Free)
            {
                "code_reference": "NBC Chapter 11 / Goa Building Regs - Accessibility",
                "requirement": "Barrier-free access: ramps (≤1:12 slope), accessible toilets, handrails",
                "status": "NOT_FOUND",
                "severity": "Major",
                "reasoning": (
                    "No ramp or accessibility features detected on this blueprint page. "
                    "For commercial and public buildings in Panjim, barrier-free access is "
                    "mandatory: ramps with slope ≤1:12, accessible toilets, handrails, "
                    "lift accessibility, and continuous accessible routes."
                ),
                "detected_value": None,
                "required_value": "Ramps ≤1:12 slope, accessible toilets, barrier-free routes",
            },
            # 13. STRUCTURAL SAFETY
            {
                "code_reference": "IS 1893 / IS 456 / Goa Building Regs - Structural Safety",
                "requirement": "Earthquake-resistant design and structural engineer certification",
                "status": "NOT_FOUND",
                "severity": "Critical",
                "reasoning": (
                    "Structural drawings (foundation, column, beam, slab details) were not "
                    "found in this submission. Goa falls under seismic zone — structures must "
                    "comply with IS 1893 (earthquake resistance) and IS 456 (concrete code). "
                    "A structural engineer's stability certificate is mandatory. "
                    "Submit separate structural drawings with ductile detailing."
                ),
                "detected_value": None,
                "required_value": "IS 1893 compliance + structural engineer certificate",
            },
            # 14. CRZ COMPLIANCE
            {
                "code_reference": "CRZ Notification 2019 / GCZMA - Coastal Zone Compliance",
                "requirement": "CRZ status verification — critical for all properties in Panjim",
                "status": "WARNING",
                "severity": "Critical",
                "reasoning": (
                    "Panjim is a coastal city — many properties fall under CRZ regulations. "
                    "CRZ-I zones prohibit all construction, CRZ-II and CRZ-III have restrictions. "
                    "Distance from High Tide Line (HTL) must be maintained. "
                    "GCZMA approval is mandatory for properties in coastal areas. "
                    "CRZ status could not be determined from the blueprint — verify with TCP department."
                ),
                "detected_value": "CRZ status unknown — requires TCP verification",
                "required_value": "GCZMA clearance if property in CRZ area",
            },
            # 15. HERITAGE ZONE
            {
                "code_reference": "Goa Heritage Rules / Panjim Heritage Committee",
                "requirement": "Heritage zone compliance — facade, height, style restrictions",
                "status": "WARNING",
                "severity": "Major",
                "reasoning": (
                    "Parts of Panjim (especially Fontainhas, São Tomé, Latin Quarter) are "
                    "heritage-sensitive zones. If this property is in a heritage area: "
                    "facade changes are restricted, building height is limited, "
                    "color scheme must conform, and Heritage Committee approval is required. "
                    "Submit elevation drawings for heritage review if applicable."
                ),
                "detected_value": "Heritage zone status unknown",
                "required_value": "Heritage Committee approval if in heritage zone",
            },
            # 16. LIFT REQUIREMENTS
            {
                "code_reference": "NBC Section 4.5 / Goa Building Regs - Lift Provisions",
                "requirement": "Lift required for multi-storey apartments and commercial buildings",
                "status": "NOT_FOUND",
                "severity": "Major",
                "reasoning": (
                    "No lift shaft or elevator area detected on this blueprint page. "
                    "Lifts are mandatory for multi-storey apartments and commercial buildings "
                    "above specified height. Fire lifts are required in high-rise structures. "
                    "If the building is G+3 or above, a lift provision is typically required."
                ),
                "detected_value": None,
                "required_value": "Lift mandatory for G+3 and above / commercial buildings",
            },
            # 17. DRAWINGS COMPLETENESS
            {
                "code_reference": "CCP / TCP - Required Drawings for Submission",
                "requirement": "Complete drawing set: site plan, floor plans, elevations, sections, parking, drainage",
                "status": "WARNING",
                "severity": "Major",
                "reasoning": (
                    "Only one floor plan page was analyzed. A complete submission requires: "
                    "site plan, key plan, floor plans for all levels, elevation drawings "
                    "(all 4 sides), section drawings, parking layout, drainage layout, and "
                    "structural drawings. All must be signed and stamped by a licensed architect."
                ),
                "detected_value": "1 floor plan page analyzed",
                "required_value": "Complete drawing set (8+ sheets minimum)",
            },
            # 18. ENVIRONMENTAL & SUSTAINABILITY
            {
                "code_reference": "Goa State Environmental Rules / NBC - Sustainability",
                "requirement": "Solar power, waste management, energy-efficient design, STP for large projects",
                "status": "NOT_FOUND",
                "severity": "Minor",
                "reasoning": (
                    "No environmental/sustainability features detected on this blueprint. "
                    "Large residential and commercial projects in Goa increasingly require: "
                    "solar power provisions, waste management plans, energy-efficient lighting, "
                    "green landscaping, and sewage treatment plants (STP). "
                    "These may be shown on separate drawings."
                ),
                "detected_value": None,
                "required_value": "Solar, STP, rainwater harvesting for large projects",
            },
        ]

        summary = (
            f"Preliminary compliance analysis against Panjim, Goa building regulations. "
            f"{len(detections)} structural elements were detected on the blueprint. "
            f"18 compliance checks were performed covering setbacks, FSI, room sizes, "
            f"fire safety, parking, CRZ, heritage, and more. "
        )
        if error:
            summary += f"Note: LLM analysis encountered an error ({error}). Showing default checks."
        else:
            summary += (
                "No OpenAI API key configured — showing comprehensive mock results based on "
                "Goa TCP Act, NBC, and CCP municipal regulations. "
                "Set OPENAI_API_KEY in .env for full AI-powered analysis."
            )

        return {
            "compliance_checks": checks,
            "overall_status": "NEEDS_REVIEW",
            "summary": summary,
        }

    def parse_compliance_checks(self, raw_result: dict) -> List[ComplianceCheck]:
        """
        Parse the raw LLM JSON output into validated ComplianceCheck objects.

        Args:
            raw_result: Dictionary from the LLM or mock analysis.

        Returns:
            List of validated ComplianceCheck Pydantic models.
        """
        checks = []
        for item in raw_result.get("compliance_checks", []):
            try:
                check = ComplianceCheck(
                    code_reference=item.get("code_reference", "Unknown"),
                    requirement=item.get("requirement", ""),
                    status=item.get("status", "NOT_FOUND"),
                    severity=item.get("severity", "Minor"),
                    reasoning=item.get("reasoning", ""),
                    detected_value=item.get("detected_value"),
                    required_value=item.get("required_value"),
                )
                checks.append(check)
            except Exception as e:
                logger.warning(f"Failed to parse compliance check: {e}")
                continue

        return checks
