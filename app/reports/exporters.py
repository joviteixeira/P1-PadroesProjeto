from __future__ import annotations
import csv, json, os
from typing import List, Dict, Any

class CSVExporter:
    def export(self, path: str, rows: List[Dict[str, Any]]) -> str:
        if not rows:
            rows = [{"msg": "sem dados"}]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        return os.path.abspath(path)

class JSONExporter:
    def export(self, path: str, rows: List[Dict[str, Any]]) -> str:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        return os.path.abspath(path)

class PDFExporter:
    def export(self, path: str, rows: List[Dict[str, Any]]) -> str:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(path, pagesize=A4)
            width, height = A4
            y = height - 50
            c.setFont("Helvetica", 12)
            c.drawString(50, y, "Relatório de Desempenho")
            y -= 30
            for row in rows:
                line = ", ".join(f"{k}: {v}" for k, v in row.items())
                if y < 50:
                    c.showPage(); y = height - 50; c.setFont("Helvetica", 12)
                c.drawString(50, y, line[:110])
                y -= 18
            c.save()
        except Exception as e:
            # Fallback: write a pseudo-PDF (txt) to keep the flow
            with open(path, "w", encoding="utf-8") as f:
                f.write("Relatório (instale reportlab para PDF real)\n\n")
                for row in rows:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
        return os.path.abspath(path)
