from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Protocol

@dataclass
class User:
    username: str
    role: str
    points: int = 0
    level: int = 1
    medals: List[str] = field(default_factory=list)

    def add_points(self, amount: int) -> None:
        self.points += amount
        self.level = max(1, 1 + self.points // 100)

    def add_medal(self, medal: str) -> None:
        if medal not in self.medals:
            self.medals.append(medal)

class UserFactory(Protocol):
    def create(self, username: str) -> User: ...

class AlunoFactory:
    def create(self, username: str) -> User:
        return User(username=username, role="ALUNO")

class ProfessorFactory:
    def create(self, username: str) -> User:
        return User(username=username, role="PROFESSOR")

class VisitanteFactory:
    def create(self, username: str) -> User:
        return User(username=username, role="VISITANTE")

FACTORIES: Dict[str, UserFactory] = {
    "ALUNO": AlunoFactory(),
    "PROFESSOR": ProfessorFactory(),
    "VISITANTE": VisitanteFactory()
}
