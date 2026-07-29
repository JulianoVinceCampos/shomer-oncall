"""Property-based tests: as invariantes do domínio devem valer para qualquer time/window.

Cada time gerado tem ao menos um membro non-observant, então todo shift é sempre
coverable (o tratamento de uncovered é testado à parte nos unit tests do allocator).
Ver docs/TESTING.md#3 e as invariantes em docs/DOMAIN.md#9.
"""

import itertools
from datetime import date, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from shomer_oncall.config import AppConfig, SchedulePolicy, Weights
from shomer_oncall.models import Location, Member, Observance, RestrictionKind, Team
from shomer_oncall.pipeline import build_schedule

pytestmark = pytest.mark.property

_LOCATIONS = [
    Location("America/Sao_Paulo", -23.55, -46.63, 760),
    Location("Asia/Jerusalem", 31.78, 35.22, 754),
    Location("Europe/London", 51.51, -0.13, 35),
    Location("America/New_York", 40.71, -74.0, 10),
]
_SHITOT = ["gra_8.5", "gra_16.1", "mga_16.1", "fixed_40", "rt_72"]


@st.composite
def teams(draw):
    n = draw(st.integers(min_value=2, max_value=5))
    members = []
    for i in range(n):
        loc = draw(st.sampled_from(_LOCATIONS))
        observant = draw(st.booleans())
        obs = None
        if observant:
            obs = Observance(
                frozenset({RestrictionKind.SHABBAT, RestrictionKind.YOM_TOV}),
                shitah=draw(st.sampled_from(_SHITOT)),
            )
        members.append(Member(id=f"m{i}", location=loc, observance=obs))
    # Garante ao menos um membro non-observant para coverability.
    members[0] = Member(id="m0", location=_LOCATIONS[0], observance=None)
    return Team(name="t", members=tuple(members), diaspora=draw(st.booleans()))


@st.composite
def windows(draw):
    start = date(2026, 1, 1) + timedelta(days=draw(st.integers(0, 330)))
    length = draw(st.integers(6, 35))
    return start, start + timedelta(days=length)


_CFG = AppConfig(policy=SchedulePolicy.DAILY, weights=Weights())


@given(team=teams(), window=windows())
@settings(max_examples=60, deadline=None)
def test_no_violation_and_full_coverage(team, window):
    ws, we = window
    bundle = build_schedule(team, ws, we, _CFG)
    # Invariante 1: nenhuma atribuição viola um restricted interval.
    assert not bundle.has_violation
    # Invariante 2: cobertura total (existe um non-observer).
    assert not bundle.allocation.uncovered
    assert len(bundle.schedule.assignments) == len(bundle.schedule.shifts)


@given(team=teams(), window=windows())
@settings(max_examples=40, deadline=None)
def test_intervals_canonical(team, window):
    ws, we = window
    bundle = build_schedule(team, ws, we, _CFG)
    for ivs in bundle.intervals_by_member.values():
        for a, b in itertools.pairwise(ivs):
            assert a.end_utc < b.start_utc  # sorted, non-overlapping, non-adjacent


@given(team=teams(), window=windows())
@settings(max_examples=30, deadline=None)
def test_deterministic_build(team, window):
    ws, we = window
    a = build_schedule(team, ws, we, _CFG)
    b = build_schedule(team, ws, we, _CFG)
    assert a.allocation.assignments == b.allocation.assignments
    assert a.allocation.load_by_member == b.allocation.load_by_member
