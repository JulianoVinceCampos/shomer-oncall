"""Serializa um schedule para iCalendar (RFC 5545) sem dependências de terceiros.

Emite um VEVENT por shift atribuído. Timestamps em UTC (sufixo Z). A saída é
determinística: eventos em ordem de shift id, ordem de campos fixa, quebras CRLF.
"""

from __future__ import annotations

from datetime import datetime

from ..models import Schedule


def _fmt_utc(value: datetime) -> str:
    return value.strftime("%Y%m%dT%H%M%SZ")


def to_ical(schedule: Schedule, *, run_id: str = "shomer") -> str:
    shifts_by_id = {s.id: s for s in schedule.shifts}
    lines: list[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//shomer-oncall//EN",
        "CALSCALE:GREGORIAN",
    ]
    for a in schedule.assignments:
        if a.member_id is None:
            continue
        s = shifts_by_id[a.shift_id]
        lines += [
            "BEGIN:VEVENT",
            f"UID:{run_id}-{a.shift_id}@shomer-oncall",
            f"DTSTART:{_fmt_utc(s.start_utc)}",
            f"DTEND:{_fmt_utc(s.end_utc)}",
            f"SUMMARY:On-call: {a.member_id}",
            f"DESCRIPTION:shift={a.shift_id} weight={s.weight} basis={'|'.join(s.basis)}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
