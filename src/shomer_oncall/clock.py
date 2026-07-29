"""Clock injetável. O functional core nunca lê o relógio de parede diretamente;
o tempo entra apenas por esta abstração, o que mantém o core determinístico
(ver docs/adr/0004 e docs/TESTING.md#determinism-contract)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    """Clock real. Usado apenas no imperative shell (adapters/CLI)."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock:
    """Clock congelado para testes e execuções reproduzíveis."""

    def __init__(self, instant: datetime) -> None:
        if instant.tzinfo is None:
            raise ValueError("FixedClock exige um instant timezone-aware")
        self._instant = instant.astimezone(UTC)

    def now(self) -> datetime:
        return self._instant
