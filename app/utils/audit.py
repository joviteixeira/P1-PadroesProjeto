from __future__ import annotations
import json, os, time
from typing import Any, Dict, List, Optional

class AuditLog:
    """Registro de ações do usuário (append-only, JSON lines)."""
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as _:
                _.write("")

    def add(self, event: str, username: Optional[str], meta: Dict[str, Any] | None = None) -> None:
        rec = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
            "event": event,
            "username": username,
            "meta": meta or {},
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def tail(self, n: int = 20) -> List[Dict[str, Any]]:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            lines = lines[-n:]
            out = []
            for ln in lines:
                ln = ln.strip()
                if not ln: 
                    continue
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
            return out
        except FileNotFoundError:
            return []
