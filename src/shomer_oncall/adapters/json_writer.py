"""Serialização JSON determinística do schedule, audit trail e métricas.

Saída estável (keys ordenadas, arredondamento de float fixo, quebras "\n") para que
inputs idênticos gerem arquivos byte-idênticos — o determinism contract
(docs/TESTING.md#determinism-contract).
"""

from __future__ import annotations

import json
from typing import Any

from ..models import Schedule


def schedule_to_dict(schedule: Schedule) -> dict[str, Any]:
    return {
        "window": {
            "from": schedule.window_start.isoformat(),
            "to": schedule.window_end.isoformat(),
            "policy": schedule.policy,
        },
        "shifts": [
            {
                "id": s.id,
                "start_utc": s.start_utc.isoformat(),
                "end_utc": s.end_utc.isoformat(),
                "weight": s.weight,
                "basis": list(s.basis),
            }
            for s in sorted(schedule.shifts, key=lambda s: s.id)
        ],
        "assignments": [
            {
                "shift": a.shift_id,
                "member": a.member_id,
                "reason": a.reason,
                "load_before": a.load_before,
                "load_after": a.load_after,
                "alternatives": list(a.alternatives),
            }
            for a in sorted(schedule.assignments, key=lambda a: a.shift_id)
        ],
    }


def dumps(obj: dict[str, Any]) -> str:
    """JSON canônico: keys ordenadas, sem espaços sobrando, terminado em newline."""
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
