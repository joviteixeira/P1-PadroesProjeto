from __future__ import annotations
from typing import List, Dict, Any
from app.reports.exporters import CSVExporter, JSONExporter, PDFExporter
from app.reports.adapters import ExternalRankingAPI, RankingAdapter

class ReportsFacade:
    def __init__(self):
        self._csv = CSVExporter()
        self._json = JSONExporter()
        self._pdf = PDFExporter()
        self._lb = RankingAdapter(ExternalRankingAPI())

    def export_all(self, basepath: str, rows: List[Dict[str, Any]]) -> dict:
        paths = {
            "csv": self._csv.export(basepath + ".csv", rows),
            "json": self._json.export(basepath + ".json", rows),
            "pdf": self._pdf.export(basepath + ".pdf", rows),
        }
        return paths

    def leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self._lb.top(limit)
