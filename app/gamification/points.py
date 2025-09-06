from __future__ import annotations
from typing import Dict, Any
from app.challenges.observers import Subject
from app.core.users import User
from app.gamification.decorators import BaseScore, DoubleXP, StreakBonus

class PointsEngine(Subject):
    """Centraliza regras de pontos e notifica conquistas (Observer)."""
    def __init__(self):
        super().__init__()

    def award(self, user: User, raw_points: int, *, double_xp=False, streak_days=0) -> int:
        score = BaseScore(raw_points)
        if double_xp:
            score = DoubleXP(score)
        if streak_days > 0:
            score = StreakBonus(score, streak_days)
        pts = score.compute()
        user.add_points(pts)
        self.notify("POINTS_GAINED", {"username": user.username, "points": pts, "total": user.points})
        # Sample auto-medals
        if user.points >= 100 and "Iniciante 100+" not in user.medals:
            user.add_medal("Iniciante 100+")
            self.notify("MEDAL_UNLOCKED", {"username": user.username, "medal": "Iniciante 100+"})
        if user.points >= 500 and "Intermediário 500+" not in user.medals:
            user.add_medal("Intermediário 500+")
            self.notify("MEDAL_UNLOCKED", {"username": user.username, "medal": "Intermediário 500+"})
        return pts
