from __future__ import annotations
from typing import List, Protocol

class AchievementComponent(Protocol):
    def name(self) -> str: ...
    def total_medals(self) -> int: ...
    def list_medals(self) -> List[str]: ...

class Medal(AchievementComponent):
    def __init__(self, title: str):
        self.title = title

    def name(self) -> str:
        return self.title

    def total_medals(self) -> int:
        return 1

    def list_medals(self) -> List[str]:
        return [self.title]

class MedalSet(AchievementComponent):
    def __init__(self, title: str):
        self.title = title
        self.children: List[AchievementComponent] = []

    def add(self, component: AchievementComponent):
        self.children.append(component)

    def name(self) -> str:
        return self.title

    def total_medals(self) -> int:
        return sum(c.total_medals() for c in self.children)

    def list_medals(self) -> List[str]:
        medals: List[str] = []
        for c in self.children:
            medals.extend(c.list_medals())
        return medals
