"""Feasibility filter: quais membros podem cobrir quais shifts.

Um par (member, shift) é feasible sse o interval do shift não intersecta nenhum dos
restricted intervals do membro. É um HARD filter — um par infeasible nunca pode ser
atribuído, garantindo a Invariante 1 (docs/DOMAIN.md#9). As listas de candidatos são
ordenadas por member id para uma alocação determinística downstream.
"""

from __future__ import annotations

from ..models import Interval, Member, Shift


def build_feasibility(
    members: list[Member],
    shifts: list[Shift],
    intervals_by_member: dict[str, list[Interval]],
) -> dict[str, list[str]]:
    """shift.id -> lista ordenada de member ids que podem cobri-lo."""
    feasible: dict[str, list[str]] = {}
    for s in shifts:
        cands: list[str] = []
        for m in members:
            ivs = intervals_by_member.get(m.id, ())
            if not any(iv.intersects(s.start_utc, s.end_utc) for iv in ivs):
                cands.append(m.id)
        feasible[s.id] = sorted(cands)
    return feasible


def has_violation(
    assignments: dict[str, str | None],
    shifts_by_id: dict[str, Shift],
    intervals_by_member: dict[str, list[Interval]],
) -> bool:
    """Recheck de segurança: confirma que nenhuma atribuição violou um restricted interval."""
    for sid, mid in assignments.items():
        if mid is None:
            continue
        s = shifts_by_id[sid]
        for iv in intervals_by_member.get(mid, ()):
            if iv.intersects(s.start_utc, s.end_utc):
                return True
    return False
