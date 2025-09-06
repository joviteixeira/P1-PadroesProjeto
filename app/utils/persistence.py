from __future__ import annotations
import json, os
from typing import Dict, Any

class JsonStore:
    def __init__(self, path: str):
        self.path = path
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def load(self) -> Dict[str, Any]:
        with open(self.path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self, data: Dict[str, Any]) -> None:
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
