"""Puertos para reloj y coordinación con el ciclo de vida de datasets demo."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from apps.core.domain.ports import DemoDatasetLifecycle


class Clock(Protocol):
    def now(self) -> datetime: ...
