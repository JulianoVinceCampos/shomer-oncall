"""Métricas de fairness, coverage e constraint.

As definições exatas vivem em docs/METRICS.md; este módulo é a implementação delas.
A fairness é medida em weighted load. Todas as funções são puras e totais (tratam
os casos degenerados all-zero / single-member sem levantar exceção).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class FairnessMetrics:
    jain: float
    gini: float
    spread: float
    equity_gap_pct: float


@dataclass(frozen=True, slots=True)
class CoverageMetrics:
    ratio: float
    uncovered: int
    violations: int


def jain_index(loads: list[float]) -> float:
    """Jain's fairness index em (0, 1]; 1.0 == perfeitamente igual."""
    n = len(loads)
    if n == 0:
        return 1.0
    denom = n * sum(v * v for v in loads)
    if denom == 0:
        return 1.0  # load all-zero é trivialmente justo
    return (sum(loads) ** 2) / denom


def gini_coefficient(loads: list[float]) -> float:
    """Gini em [0, 1]; 0 == igualdade perfeita."""
    n = len(loads)
    total = sum(loads)
    if n == 0 or total == 0:
        return 0.0
    abs_diffs = sum(abs(a - b) for a in loads for b in loads)
    return abs_diffs / (2 * n * total)


def weighted_spread(loads: list[float]) -> float:
    if not loads:
        return 0.0
    return max(loads) - min(loads)


def equity_gap(load_by_member: dict[str, float], observer_ids: set[str]) -> tuple[float, float]:
    """(gap absoluto, gap como fração da equal share) entre a média de load dos
    observers e dos non-observers. Retorna (0, 0) se algum grupo for vazio."""
    obs = [v for m, v in load_by_member.items() if m in observer_ids]
    non = [v for m, v in load_by_member.items() if m not in observer_ids]
    if not obs or not non:
        return 0.0, 0.0
    gap = abs(sum(obs) / len(obs) - sum(non) / len(non))
    total = sum(load_by_member.values())
    equal_share = total / len(load_by_member) if load_by_member else 0.0
    gap_pct = gap / equal_share if equal_share > 0 else 0.0
    return gap, gap_pct


def compute_fairness(
    load_by_member: dict[str, float], observer_ids: set[str]
) -> FairnessMetrics:
    loads = list(load_by_member.values())
    _, gap_pct = equity_gap(load_by_member, observer_ids)
    return FairnessMetrics(
        jain=round(jain_index(loads), 6),
        gini=round(gini_coefficient(loads), 6),
        spread=round(weighted_spread(loads), 6),
        equity_gap_pct=round(gap_pct * 100.0, 4),
    )


def compute_coverage(total_shifts: int, uncovered: int, violations: int) -> CoverageMetrics:
    covered = total_shifts - uncovered
    ratio = (covered / total_shifts) if total_shifts else 1.0
    return CoverageMetrics(ratio=round(ratio, 6), uncovered=uncovered, violations=violations)


def as_dict(fairness: FairnessMetrics, coverage: CoverageMetrics) -> dict[str, Any]:
    return {"fairness": asdict(fairness), "coverage": asdict(coverage)}
