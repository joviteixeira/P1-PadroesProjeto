from __future__ import annotations
from typing import Optional
from dataclasses import dataclass

@dataclass
class SessionUser:
    username: str
    role: str

class _SessionSingleton:
    _instance: Optional['_SessionSingleton'] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.current_user = None
        return cls._instance

    def login(self, username: str, role: str) -> None:
        self.current_user = SessionUser(username=username, role=role)

    def logout(self) -> None:
        self.current_user = None

    def is_authenticated(self) -> bool:
        return self.current_user is not None

def get_session() -> _SessionSingleton:
    """Global access point to the Session (Singleton)."""
    return _SessionSingleton()
