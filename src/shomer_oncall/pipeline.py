"""Orquestração do pipeline: time + window + config -> schedule + intervals + loads.

É o único lugar onde os stages puros são ligados. Não faz I/O; o CLI shell trata
arquivos e impressão (functional core, imperative shell).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .calendar.engine import restricted_intervals
from .config import AppConfig
from .models import Interval, Member, Schedule, Team
from .scheduling.allocator import AllocationResult, allocate
from .scheduling.feasibility import build_feasibility, has_violation
from .scheduling.generator import generate_shifts


@dataclass(frozen=True, slots=True)
class ScheduleBundle:
    schedule: Schedule
    intervals_by_member: dict[str, list[Interval]]
    allocation: AllocationResult
    has_violation: bool


def build_schedule(
    team: Team,
    window_start: date,
    window_end: date,
    config: AppConfig,
    history: dict[str, float] | None = None,
) -> ScheduleBundle:
    members: list[Member] = list(team.members)

    intervals_by_member: dict[str, list[Interval]] = {}
    for m in members:
        if m.observes_anything:
            intervals_by_member[m.id] = restricted_intervals(
                m, window_start, window_end, team.diaspora_for(m)
            )

    shifts = generate_shifts(
        window_start,
        window_end,
        config.policy,
        config.weights,
        config.handoff_hour_local,
    )
    feasible = build_feasibility(members, shifts, intervals_by_member)
    result = allocate(shifts, feasible, [m.id for m in members], history)

    schedule = Schedule(
        window_start=window_start,
        window_end=window_end,
        policy=config.policy.value,
        shifts=tuple(shifts),
        assignments=result.assignments,
    )
    shifts_by_id = {s.id: s for s in shifts}
    violation = has_violation(
        {a.shift_id: a.member_id for a in result.assignments},
        shifts_by_id,
        intervals_by_member,
    )
    return ScheduleBundle(
        schedule=schedule,
        intervals_by_member=intervals_by_member,
        allocation=result,
        has_violation=violation,
    )
