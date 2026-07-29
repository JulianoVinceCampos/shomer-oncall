"""Calendar engine: canonicidade de intervals, merge e gating de observance."""

import itertools
from datetime import date

from shomer_oncall.calendar.engine import restricted_intervals
from shomer_oncall.models import Location, Member, Observance, RestrictionKind

SP = Location("America/Sao_Paulo", -23.55, -46.63, 760)


def _observant(**kw):
    cats = kw.get("categories", frozenset({RestrictionKind.SHABBAT, RestrictionKind.YOM_TOV}))
    return Member(id="m", location=SP, observance=Observance(cats))


def test_non_observer_has_no_intervals():
    m = Member(id="alex", location=SP, observance=None)
    assert restricted_intervals(m, date(2026, 1, 1), date(2026, 12, 31), True) == []


def test_shabbat_count_matches_saturdays_in_january():
    m = _observant(categories=frozenset({RestrictionKind.SHABBAT}))
    ivs = restricted_intervals(m, date(2026, 1, 1), date(2026, 1, 31), True)
    # Janeiro de 2026 tem sábados em 3,10,17,24,31 -> 5 Shabbatot.
    assert len(ivs) == 5
    assert all(iv.kind is RestrictionKind.SHABBAT for iv in ivs)


def test_intervals_are_sorted_and_non_overlapping():
    m = _observant()
    ivs = restricted_intervals(m, date(2026, 1, 1), date(2026, 12, 31), True)
    for a, b in itertools.pairwise(ivs):
        assert a.end_utc < b.start_utc


def test_two_day_diaspora_yomtov_merges_into_one_interval():
    m = _observant(categories=frozenset({RestrictionKind.YOM_TOV}))
    # Shavuot 5786 = 6-7 Sivan (2026-05-22/23). Diaspora => interval único mesclado.
    ivs = restricted_intervals(m, date(2026, 5, 20), date(2026, 5, 26), True)
    assert len(ivs) == 1
    hours = (ivs[0].end_utc - ivs[0].start_utc).total_seconds() / 3600
    assert 44 <= hours <= 52  # ~2 dias mais buffer


def test_shabbat_interval_is_about_25_hours():
    m = _observant(categories=frozenset({RestrictionKind.SHABBAT}))
    ivs = restricted_intervals(m, date(2026, 6, 1), date(2026, 6, 30), True)
    for iv in ivs:
        hours = (iv.end_utc - iv.start_utc).total_seconds() / 3600
        assert 24 <= hours <= 26


def test_rationale_present_and_explains_endpoints():
    m = _observant(categories=frozenset({RestrictionKind.SHABBAT}))
    iv = restricted_intervals(m, date(2026, 6, 1), date(2026, 6, 30), True)[0]
    assert iv.rationale["start"]["buffer_min"] == 18
    assert iv.rationale["end"]["shitah"] == "gra_8.5"
