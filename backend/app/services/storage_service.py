"""
AutoPermit AI — Storage Service
In-memory report storage (swappable to Supabase/PostgreSQL).
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from app.schemas import ComplianceReport, ReportListItem

logger = logging.getLogger(__name__)


class StorageService:
    """
    In-memory storage for compliance reports.

    This is a development-mode store. For production, swap this with a
    Supabase/PostgreSQL implementation using the same interface.
    """

    def __init__(self):
        self._reports: Dict[str, ComplianceReport] = {}

    def save_report(self, report: ComplianceReport) -> None:
        """Save or update a compliance report."""
        self._reports[report.report_id] = report
        logger.info(f"Saved report: {report.report_id} ({report.filename})")

    def get_report(self, report_id: str) -> Optional[ComplianceReport]:
        """Retrieve a report by ID."""
        return self._reports.get(report_id)

    def list_reports(self) -> List[ReportListItem]:
        """List all reports (lightweight summaries)."""
        items = []
        for r in sorted(
            self._reports.values(),
            key=lambda x: x.created_at,
            reverse=True,
        ):
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
        """Delete a report by ID. Returns True if found and deleted."""
        if report_id in self._reports:
            del self._reports[report_id]
            logger.info(f"Deleted report: {report_id}")
            return True
        return False

    @property
    def count(self) -> int:
        """Total number of stored reports."""
        return len(self._reports)
