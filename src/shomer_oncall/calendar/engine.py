"""Calendar engine: membro + window -> restricted intervals canônicos.

Unifica Shabbat (semanal) e festivais calendar-anchored numa única regra: um dia
gregoriano restrito D vai de sunset(D-1) - buffer até tzais(D). Dias de festival/
Shabbat adjacentes portanto se sobrepõem e são mesclados num único interval, que é
exatamente o caso Yom-Tov-encosta-em-Shabbat (docs/DOMAIN.md#6). A saída é sorted,
não-sobreposta, não-adjacente (Invariante 3).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from ..models import Interval, Member, RestrictionKind
from . import astronomy, holidays
from .hebrew import date_from_fixed, fixed_from_date, hebrew_year_of
from .zmanim_opinions import Opinion, get_opinion

_KIND_PRIORITY = {
    RestrictionKind.YOM_TOV: 3,
    RestrictionKind.SHABBAT: 3,
    RestrictionKind.CHOL_HAMOED: 2,
    RestrictionKind.FAST: 1,
}


def _stronger(a: RestrictionKind | None, b: RestrictionKind) -> RestrictionKind:
    if a is None or _KIND_PRIORITY[b] > _KIND_PRIORITY[a]:
        return b
    return a


def _tzais(d: date, lat: float, lon: float, elev: float, op: Opinion) -> tuple[datetime, bool]:
    """Retorna (nightfall_utc, used_fallback)."""
    if op.is_angular():
        assert op.depression_deg is not None  # is_angular() garante isto
        try:
            return (
                astronomy.nightfall(d.year, d.month, d.day, lat, lon, elev, op.depression_deg),
                False,
            )
        except astronomy.NoSolarEventError:
            ss = astronomy.sunset(d.year, d.month, d.day, lat, lon, elev)
            return ss + timedelta(minutes=op.fallback_minutes), True
    assert op.fixed_minutes is not None  # opinião não-angular => minutes definido
    ss = astronomy.sunset(d.year, d.month, d.day, lat, lon, elev)
    return ss + timedelta(minutes=op.fixed_minutes), False


def _interval_for_day(
    d: date,
    kind: RestrictionKind,
    lat: float,
    lon: float,
    elev: float,
    buffer_min: int,
    op: Opinion,
) -> Interval:
    prev = d - timedelta(days=1)
    ss_prev = astronomy.sunset(prev.year, prev.month, prev.day, lat, lon, elev)
    start = ss_prev - timedelta(minutes=buffer_min)
    end, fellback = _tzais(d, lat, lon, elev, op)
    rationale = {
        "date": d.isoformat(),
        "kind": kind.value,
        "start": {"event": "shkiah", "eve": prev.isoformat(), "buffer_min": buffer_min},
        "end": {
            "event": "tzais",
            "shitah": op.key,
            "depression_deg": op.depression_deg,
            "fixed_minutes": op.fixed_minutes,
            "fallback": fellback,
        },
        "location": {"lat": lat, "lon": lon, "elevation_m": elev},
    }
    return Interval(start_utc=start, end_utc=end, kind=kind, rationale=rationale)


def _merge_adjacent(intervals: list[Interval]) -> list[Interval]:
    intervals = sorted(intervals, key=lambda iv: iv.start_utc)
    out: list[Interval] = []
    for iv in intervals:
        if out and iv.start_utc <= out[-1].end_utc:  # sobreposição OU encosta
            prev = out[-1]
            merged_kind = _stronger(prev.kind, iv.kind)
            rationale = prev.rationale
            if iv.end_utc > prev.end_utc:
                rationale = {**prev.rationale, "merged_end": iv.rationale}
            out[-1] = Interval(
                start_utc=prev.start_utc,
                end_utc=max(prev.end_utc, iv.end_utc),
                kind=merged_kind,
                rationale=rationale,
            )
        else:
            out.append(iv)
    return out


def restricted_intervals(
    member: Member, window_start: date, window_end: date, diaspora: bool
) -> list[Interval]:
    """Restricted intervals canônicos de `member` que sobrepõem a window."""
    if not member.observes_anything:
        return []
    obs = member.observance
    assert obs is not None
    op = get_opinion(obs.shitah)
    loc = member.location
    categories = obs.categories

    # Padding de 2 dias para capturar Shabbat/festival que atravessa a borda da window.
    start_f = fixed_from_date(window_start) - 2
    end_f = fixed_from_date(window_end) + 2

    day_kinds: dict[date, RestrictionKind] = {}

    if RestrictionKind.SHABBAT in categories:
        for f in range(start_f, end_f + 1):
            d = date_from_fixed(f)
            if d.weekday() == 5:  # sábado (Mon=0 .. Sun=6)
                day_kinds[d] = _stronger(day_kinds.get(d), RestrictionKind.SHABBAT)

    if categories & {RestrictionKind.YOM_TOV, RestrictionKind.CHOL_HAMOED, RestrictionKind.FAST}:
        hy0 = hebrew_year_of(date_from_fixed(start_f))
        hy1 = hebrew_year_of(date_from_fixed(end_f))
        for hy in range(hy0, hy1 + 2):
            for rd, kind in holidays.restricted_days(hy, diaspora, categories).items():
                if start_f <= rd <= end_f:
                    d = date_from_fixed(rd)
                    day_kinds[d] = _stronger(day_kinds.get(d), kind)

    raw = [
        _interval_for_day(
            d, kind, loc.latitude, loc.longitude, loc.elevation_m, obs.candle_buffer_min, op
        )
        for d, kind in sorted(day_kinds.items())
    ]
    return _merge_adjacent(raw)


def boundary_for(d: date, member: Member, diaspora: bool) -> Interval | None:
    """Restricted interval que contém (ou está ao redor de) a data `d`, para o
    comando `explain-boundary`. Retorna None se `d` não é restrito."""
    ivs = restricted_intervals(member, d - timedelta(days=2), d + timedelta(days=2), diaspora)
    # Casamento por contenção de data-calendário ao longo do span do interval.
    for iv in ivs:
        if iv.start_utc.date() <= d <= iv.end_utc.date():
            return iv
    return None
