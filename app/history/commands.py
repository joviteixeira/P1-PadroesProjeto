from __future__ import annotations
from typing import Protocol, List, Optional
from app.core.users import User

class Command(Protocol):
    def execute(self) -> None: ...
    def undo(self) -> None: ...

class History:
    def __init__(self):
        self._stack: List[Command] = []

    def push_and_exec(self, cmd: Command) -> None:
        cmd.execute()
        self._stack.append(cmd)

    def undo_last(self) -> Optional[str]:
        if not self._stack:
            return "Nada para desfazer."
        cmd = self._stack.pop()
        cmd.undo()
        return f"Desfeito: {cmd.__class__.__name__}"

class AwardPointsCommand:
    def __init__(self, user: User, amount: int):
        self.user = user
        self.amount = amount

    def execute(self) -> None:
        self._before = self.user.points
        self.user.add_points(self.amount)

    def undo(self) -> None:
        self.user.points = self._before
        # level recalculated simply
        self.user.level = max(1, 1 + self.user.points // 100)

class AwardMedalCommand:
    def __init__(self, user: User, medal: str):
        self.user = user
        self.medal = medal

    def execute(self) -> None:
        self._had = self.medal in self.user.medals
        if not self._had:
            self.user.add_medal(self.medal)

    def undo(self) -> None:
        if not self._had and self.medal in self.user.medals:
            self.user.medals.remove(self.medal)

from typing import Optional
from app.gamification.points import PointsEngine

class QuizAttemptCommand:
    """Executa a premiação via PointsEngine e permite desfazer restaurando snapshot."""
    def __init__(self, user: User, engine: PointsEngine, raw_points: int, double_xp: bool, streak_days: int):
        self.user = user
        self.engine = engine
        self.raw_points = raw_points
        self.double_xp = double_xp
        self.streak_days = streak_days
        self._before_points: Optional[int] = None
        self._before_level: Optional[int] = None
        self._before_medals: Optional[list] = None
        self.last_awarded: Optional[int] = None

    def execute(self) -> None:
        # snapshot do estado do usuário
        self._before_points = self.user.points
        self._before_level = self.user.level
        self._before_medals = list(self.user.medals)
        # premia e guarda o quanto foi realmente creditado (decorators aplicados)
        self.last_awarded = self.engine.award(self.user, self.raw_points, double_xp=self.double_xp, streak_days=self.streak_days)

    def undo(self) -> None:
        if self._before_points is not None:
            self.user.points = self._before_points
        if self._before_level is not None:
            self.user.level = self._before_level
        if self._before_medals is not None:
            self.user.medals = list(self._before_medals)
