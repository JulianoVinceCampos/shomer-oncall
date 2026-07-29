"""Value objects do domínio.

Dataclasses simples e imutáveis (sem dependência de terceiros). Todos os instants
são timezone-aware em UTC (docs/adr/0004). São os objetos sobre os quais o
functional core opera; os adapters traduzem arquivos de/para eles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any


class RestrictionKind(StrEnum):
    SHABBAT = "shabbat"
    YOM_TOV = "yom_tov"
    CHOL_HAMOED = "chol_hamoed"
    FAST = "fast"


# Categorias que bloqueiam o plantão por padrão (consenso amplo de que atuar num
# page não é permitido). Categorias mais brandas são opt-in (docs/DOMAIN.md#3).
DEFAULT_BLOCKING = frozenset({RestrictionKind.SHABBAT, RestrictionKind.YOM_TOV})


@dataclass(frozen=True, slots=True)
class Location:
    timezone: str
    latitude: float
    longitude: float
    elevation_m: float = 0.0

    def __post_init__(self) -> None:
        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError(f"latitude fora do intervalo: {self.latitude}")
        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError(f"longitude fora do intervalo: {self.longitude}")


@dataclass(frozen=True, slots=True)
class Observance:
    categories: frozenset[RestrictionKind]
    candle_buffer_min: int = 18
    shitah: str = "gra_8.5"


@dataclass(frozen=True, slots=True)
class Member:
    id: str
    location: Location
    observance: Observance | None = None  # None => sem restrições de calendário
    diaspora: bool | None = None  # sobrescreve o default do time quando definido

    @property
    def observes_anything(self) -> bool:
        return self.observance is not None and bool(self.observance.categories)


@dataclass(frozen=True, slots=True)
class Team:
    name: str
    members: tuple[Member, ...]
    diaspora: bool = True

    def diaspora_for(self, member: Member) -> bool:
        return member.diaspora if member.diaspora is not None else self.diaspora


@dataclass(frozen=True, slots=True)
class Interval:
    """Janela de tempo em UTC durante a qual um membro não pode ser paginado."""

    start_utc: datetime
    end_utc: datetime
    kind: RestrictionKind
    rationale: dict[str, Any] = field(default_factory=dict, compare=False)

    def intersects(self, start: datetime, end: datetime) -> bool:
        return self.start_utc < end and start < self.end_utc


@dataclass(frozen=True, slots=True)
class Shift:
    id: str
    start_utc: datetime
    end_utc: datetime
    weight: float
    basis: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Assignment:
    shift_id: str
    member_id: str | None  # None => uncovered
    reason: str
    load_before: float = 0.0
    load_after: float = 0.0
    alternatives: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Schedule:
    window_start: date
    window_end: date
    policy: str
    shifts: tuple[Shift, ...]
    assignments: tuple[Assignment, ...]

    @property
    def uncovered(self) -> tuple[Assignment, ...]:
        return tuple(a for a in self.assignments if a.member_id is None)
