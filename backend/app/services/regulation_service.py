"""
AutoPermit AI — Regulation Service
Handles searching and retrieval of building regulations.
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class RegulationService:
    def __init__(self, regulation_path: str):
        self.regulation_path = Path(regulation_path)
        self.content = ""
        self.sections = []
        self._load_regulations()

    def _load_regulations(self):
        """Load and parse the regulations text file into sections."""
        if not self.regulation_path.exists():
            logger.warning(f"Regulation file not found at {self.regulation_path}")
            return

        try:
            with open(self.regulation_path, "r", encoding="utf-8") as f:
                self.content = f.read()
            
            # Simple section splitting based on typical headers like "1.", "2.", "Chapter", etc.
            # This is a heuristic and can be improved.
            self.sections = re.split(r'\n(?=\d+\.\s|[A-Z][A-Z\s]+\d+\n)', self.content)
            logger.info(f"Loaded regulations: {len(self.sections)} sections identified.")
        except Exception as e:
            logger.error(f"Failed to load regulations: {e}")

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search for relevant sections based on a query.
        For now, uses simple keyword matching. 
        Could be upgraded to semantic search (embeddings) later.
        """
        if not query:
            return []

        query = query.lower()
        results = []
        
        for i, section in enumerate(self.sections):
            if query in section.lower():
                # Extract a title/snippet
                lines = section.strip().split('\n')
                title = lines[0] if lines else f"Section {i}"
                results.append({
                    "id": i,
                    "title": title,
                    "content": section.strip(),
                    "score": 1.0  # Simple match score
                })
        
        # Sort by relevance (basic: length of match or position)
        return results[:limit]

    def get_all_regulations(self) -> str:
        """Return the entire content (useful for small context windows or summary)."""
        return self.content
