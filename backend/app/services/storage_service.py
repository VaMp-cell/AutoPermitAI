"""
AutoPermit AI — Storage Service
Handles persistent report storage using local JSON files.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from app.schemas import ComplianceReport, ReportListItem
from app.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.output_dir = Path(settings.OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._reports: Dict[str, ComplianceReport] = {}
        self._load_from_disk()

    def _load_from_disk(self):
        """Load all reports from individual JSON files in the output directory."""
        logger.info(f"Loading reports from {self.output_dir}...")
        count = 0
        for report_folder in self.output_dir.iterdir():
            if report_folder.is_dir():
                report_file = report_folder / "report.json"
                if report_file.exists():
                    try:
                        with open(report_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            # Pydantic 2.0+ uses model_validate_json or model_validate
                            report = ComplianceReport.model_validate(data)
                            self._reports[report.report_id] = report
                            count += 1
                    except Exception as e:
                        logger.error(f"Failed to load report {report_folder.name}: {e}")
        logger.info(f"Successfully loaded {count} reports from disk.")

    def save_report(self, report: ComplianceReport) -> None:
        """Save report to memory and persist to disk."""
        self._reports[report.report_id] = report
        
        # Persist to disk
        report_dir = self.output_dir / report.report_id
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / "report.json"
        
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                # Use model_dump_json() or json.dumps(model_dump())
                f.write(report.model_dump_json(indent=2))
            logger.info(f"Persisted report {report.report_id} to disk.")
        except Exception as e:
            logger.error(f"Failed to persist report {report.report_id}: {e}")

    def get_report(self, report_id: str) -> Optional[ComplianceReport]:
        return self._reports.get(report_id)

    def list_reports(self) -> List[ReportListItem]:
        items = []
        # Sort by creation date descending
        sorted_reports = sorted(
            self._reports.values(),
            key=lambda x: x.created_at,
            reverse=True
        )
        for r in sorted_reports:
            items.append(
                ReportListItem(
                    report_id=r.report_id,
                    filename=r.filename,
                    created_at=r.created_at,
                    overall_status=r.overall_status,
                    detection_count=len(r.detections),
                    check_count=len(r.compliance_checks),
                )
            )
        return items

    def delete_report(self, report_id: str) -> bool:
        if report_id in self._reports:
            del self._reports[report_id]
            # Delete from disk
            report_dir = self.output_dir / report_id
            if report_dir.exists():
                import shutil
                shutil.rmtree(report_dir)
            logger.info(f"Deleted report {report_id} from memory and disk.")
            return True
        return False

    @property
    def count(self) -> int:
        return len(self._reports)
