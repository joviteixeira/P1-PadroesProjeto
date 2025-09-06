from __future__ import annotations
from typing import Protocol, Dict, Any

class ScoringStrategy(Protocol):
    def score(self, context: Dict[str, Any]) -> int: ...

class DifficultyStrategy:
    def score(self, context: Dict[str, Any]) -> int:
        # base points proportional to difficulty
        base = 50 * max(1, int(context.get("difficulty", 1)))
        return base

class AccuracyStrategy:
    def score(self, context: Dict[str, Any]) -> int:
        acc = float(context.get("accuracy", 0.0))
        return int(200 * acc)

class TimeStrategy:
    def score(self, context: Dict[str, Any]) -> int:
        # Faster is better: time in seconds
        t = float(context.get("time_sec", 9999))
        if t <= 30: return 200
        if t <= 60: return 120
        if t <= 120: return 60
        return 20

class CompositeStrategy:
    """Combine multiple strategies (simple sum)."""
    def __init__(self, *strategies: ScoringStrategy):
        self.strategies = strategies

    def score(self, context: Dict[str, Any]) -> int:
        return sum(s.score(context) for s in self.strategies)
