"""Alocação justa.

Atribui cada shift a exatamente um membro feasible, minimizando o desbalanceamento
de weighted load no time ao longo de um rolling horizon (history carry-in). A
estratégia entregue é um weighted least-loaded greedy determinístico (shift mais
pesado primeiro) seguido de local search redutor de variância (docs/ALGORITHMS.md#5).
Ambos respeitam as constraints hard de feasibility/coverage; ambos são determinísticos.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..models import Assignment, Shift

_LOCAL_SEARCH_BUDGET = 5000


@dataclass(frozen=True, slots=True)
class AllocationResult:
    assignments: tuple[Assignment, ...]
    load_by_member: dict[str, float]
    uncovered: tuple[str, ...]


def _variance(load: dict[str, float]) -> float:
    if not load:
        return 0.0
    mean = sum(load.values()) / len(load)
    return sum((v - mean) ** 2 for v in load.values())


def _local_search(
    assign: dict[str, str],
    load: dict[str, float],
    weight_by_shift: dict[str, float],
    feasible: dict[str, list[str]],
) -> None:
    """Moves de reatribuição redutores de variância, in-place. Determinístico: shifts
    percorridos em ordem de id, candidatos em ordem ordenada, empates não movem
    (fixpoint estável)."""
    iters = 0
    improved = True
    while improved and iters < _LOCAL_SEARCH_BUDGET:
        improved = False
        for sid in sorted(assign):
            current = assign[sid]
            w = weight_by_shift[sid]
            base_obj = _variance(load)
            best_obj = base_obj
            best_m = current
            for cand in feasible[sid]:
                if cand == current:
                    continue
                load[current] -= w
                load[cand] += w
                obj = _variance(load)
                load[current] += w
                load[cand] -= w
                if obj < best_obj - 1e-9:
                    best_obj = obj
                    best_m = cand
            if best_m != current:
                load[current] -= w
                load[best_m] += w
                assign[sid] = best_m
                improved = True
                iters += 1


def allocate(
    shifts: list[Shift],
    feasible: dict[str, list[str]],
    member_ids: list[str],
    history: dict[str, float] | None = None,
) -> AllocationResult:
    history = history or {}
    load: dict[str, float] = {mid: float(history.get(mid, 0.0)) for mid in member_ids}
    weight_by_shift = {s.id: s.weight for s in shifts}

    assign: dict[str, str] = {}
    uncovered: list[str] = []
    audit_before: dict[str, float] = {}

    # Greedy: shift mais pesado primeiro, atribui ao membro feasible menos carregado.
    for s in sorted(shifts, key=lambda sh: (-sh.weight, sh.id)):
        cands = feasible[s.id]
        if not cands:
            uncovered.append(s.id)
            continue
        chosen = min(cands, key=lambda mid: (load[mid], mid))
        audit_before[s.id] = load[chosen]
        load[chosen] += s.weight
        assign[s.id] = chosen

    _local_search(assign, load, weight_by_shift, feasible)

    # Monta os records de assignment (em ordem de shift) com rationale.
    assignments: list[Assignment] = []
    for s in sorted(shifts, key=lambda sh: sh.id):
        mid = assign.get(s.id)
        if mid is None:
            assignments.append(Assignment(shift_id=s.id, member_id=None, reason="uncovered"))
            continue
        alts = tuple(f"{c}(load {load[c]:.2f})" for c in feasible[s.id] if c != mid)
        assignments.append(
            Assignment(
                shift_id=s.id,
                member_id=mid,
                reason="least_loaded_feasible",
                load_before=round(audit_before.get(s.id, 0.0), 6),
                load_after=round(load[mid], 6),
                alternatives=alts,
            )
        )
    return AllocationResult(
        assignments=tuple(assignments),
        load_by_member={k: round(v, 6) for k, v in load.items()},
        uncovered=tuple(sorted(uncovered)),
    )
