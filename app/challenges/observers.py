from __future__ import annotations
from typing import Protocol, List, Dict, Any

class Observer(Protocol):
    def update(self, event: str, payload: Dict[str, Any]) -> None: ...

class Subject:
    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, obs: Observer) -> None:
        if obs not in self._observers:
            self._observers.append(obs)

    def detach(self, obs: Observer) -> None:
        if obs in self._observers:
            self._observers.remove(obs)

    def notify(self, event: str, payload: Dict[str, Any]) -> None:
        for obs in list(self._observers):
            obs.update(event, payload)

class ConsoleNotifier:
    def update(self, event: str, payload: Dict[str, Any]) -> None:
        if event == "POINTS_GAINED":
            print(f"[NOTIF] {payload['username']} ganhou {payload['points']} pontos (total={payload['total']}).")
        elif event == "MEDAL_UNLOCKED":
            print(f"[NOTIF] {payload['username']} desbloqueou a medalha: {payload['medal']}.")

from app.utils.audit import AuditLog

class AuditObserver:
    """Observer que grava eventos no AuditLog."""
    def __init__(self, audit: AuditLog):
        self.audit = audit

    def update(self, event: str, payload: Dict[str, Any]) -> None:
        username = payload.get("username")
        if event == "POINTS_GAINED":
            self.audit.add("POINTS_GAINED", username, {"points": payload.get("points"), "total": payload.get("total")})
        elif event == "MEDAL_UNLOCKED":
            self.audit.add("MEDAL_UNLOCKED", username, {"medal": payload.get("medal")})
