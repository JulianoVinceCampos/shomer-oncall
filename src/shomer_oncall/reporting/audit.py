"""Montagem do audit trail.

O audit trail é o registro autoritativo e machine-readable do *porquê* de cada
boundary e cada assignment (docs/OBSERVABILITY.md#2). É montado a partir dos
rationales dos intervals (boundary records) e dos rationales de assignment.
"""

from __future__ import annotations

from typing import Any

from ..models import Interval, Schedule


def build_audit(
    intervals_by_member: dict[str, list[Interval]], schedule: Schedule
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for member_id in sorted(intervals_by_member):
        for iv in intervals_by_member[member_id]:
            records.append(
                {
                    "type": "boundary",
                    "member": member_id,
                    "kind": iv.kind.value,
                    "start_utc": iv.start_utc.isoformat(),
                    "end_utc": iv.end_utc.isoformat(),
                    "rationale": iv.rationale,
                }
            )

    for a in schedule.assignments:
        records.append(
            {
                "type": "assignment",
                "shift": a.shift_id,
                "member": a.member_id,
                "reason": a.reason,
                "load_before": a.load_before,
                "load_after": a.load_after,
                "alternatives": list(a.alternatives),
            }
        )

    return records
