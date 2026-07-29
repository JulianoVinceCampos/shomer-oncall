"""Load model: atribui um burden weight a um dia de shift.

A fairness é medida em weight, não em contagem bruta de shifts, porque um shift de
fim de semana/feriado é mais pesado (docs/ALGORITHMS.md#3). Dias de fim de semana
(Fri/Sat/Sun) carregam o weekend multiplier; company holidays (se fornecidos)
carregam o holiday multiplier.
"""

from __future__ import annotations

from datetime import date, datetime

from ..config import Weights

_WEEKEND_WEEKDAYS = frozenset({4, 5, 6})  # Fri, Sat, Sun (Mon=0 .. Sun=6)


def day_weight(
    day_start_utc: datetime, weights: Weights, company_holidays: frozenset[date]
) -> tuple[float, tuple[str, ...]]:
    basis: list[str] = ["base"]
    w = weights.base
    if day_start_utc.weekday() in _WEEKEND_WEEKDAYS:
        w *= weights.weekend_mult
        basis.append("weekend")
    if day_start_utc.date() in company_holidays:
        w *= weights.holiday_mult
        basis.append("holiday")
    return w, tuple(basis)
