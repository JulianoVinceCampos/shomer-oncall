"""Geração de shifts. Os shifts recobrem a window sem gaps.

Shifts são ancorados numa handoff hour fixa em UTC (mantém a geração determinística
e timezone-agnostic; a observance por membro é aplicada depois, na feasibility). Um
shift daily cobre 24h; um shift weekly cobre 7 dias e pesa a soma dos seus dias
(docs/ARCHITECTURE.md#6).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from ..config import SchedulePolicy, Weights
from ..models import Shift
from .weights import day_weight


def _handoff(d: date, hour: int) -> datetime:
    return datetime(d.year, d.month, d.day, hour, tzinfo=UTC)


def generate_shifts(
    window_start: date,
    window_end: date,
    policy: SchedulePolicy,
    weights: Weights,
    handoff_hour: int,
    company_holidays: frozenset[date] = frozenset(),
) -> list[Shift]:
    if window_end < window_start:
        raise ValueError("window_end é anterior a window_start")

    shifts: list[Shift] = []
    if policy is SchedulePolicy.DAILY:
        d = window_start
        while d <= window_end:
            start = _handoff(d, handoff_hour)
            w, basis = day_weight(start, weights, company_holidays)
            shifts.append(
                Shift(id=d.isoformat(), start_utc=start, end_utc=start + timedelta(days=1),
                      weight=w, basis=basis)
            )
            d += timedelta(days=1)
    elif policy is SchedulePolicy.WEEKLY:
        d = window_start
        while d <= window_end:
            start = _handoff(d, handoff_hour)
            end = start + timedelta(days=7)
            total = 0.0
            bases: set[str] = set()
            for k in range(7):
                dw, basis = day_weight(start + timedelta(days=k), weights, company_holidays)
                total += dw
                bases.update(basis)
            shifts.append(
                Shift(id=f"week-{d.isoformat()}", start_utc=start, end_utc=end,
                      weight=round(total, 6), basis=tuple(sorted(bases)))
            )
            d += timedelta(days=7)
    else:  # pragma: no cover - enum tratado exaustivamente
        raise ValueError(f"policy não suportada: {policy}")
    return shifts
