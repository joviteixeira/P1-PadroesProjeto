from __future__ import annotations

class Score:
    def compute(self) -> int:
        return 0

class BaseScore(Score):
    def __init__(self, points: int):
        self._points = points
    def compute(self) -> int:
        return self._points

class ScoreDecorator(Score):
    def __init__(self, inner: Score):
        self._inner = inner
    def compute(self) -> int:
        return self._inner.compute()

class DoubleXP(ScoreDecorator):
    def compute(self) -> int:
        return 2 * super().compute()

class StreakBonus(ScoreDecorator):
    def __init__(self, inner: Score, streak_days: int):
        super().__init__(inner)
        self._streak_days = streak_days
    def compute(self) -> int:
        base = super().compute()
        # +10% per day, capped at +100%
        bonus = min(self._streak_days, 10) * 0.10
        return int(base * (1 + bonus))
