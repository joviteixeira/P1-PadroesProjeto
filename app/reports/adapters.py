from __future__ import annotations
from typing import List, Dict, Any

class ExternalRankingAPI:
    """Simula um serviço externo com formato próprio (adaptee)."""
    def fetch_top(self, limit: int = 10) -> List[Dict[str, Any]]:
        # formato estranho: [{'u': 'nome', 'p': pontos}]
        dummy = [
            {"u": "alice", "p": 420},
            {"u": "bob", "p": 300},
            {"u": "carol", "p": 180},
        ]
        return dummy[:limit]

class Leaderboard:
    """Target interface esperada pelo sistema interno."""
    def top(self, limit: int = 10) -> List[Dict[str, Any]]:
        raise NotImplementedError

class RankingAdapter(Leaderboard):
    def __init__(self, external_api: ExternalRankingAPI):
        self.external_api = external_api

    def top(self, limit: int = 10) -> List[Dict[str, Any]]:
        raw = self.external_api.fetch_top(limit)
        # adapta para [{'username':..., 'points':...}]
        return [{"username": r["u"], "points": r["p"]} for r in raw]
