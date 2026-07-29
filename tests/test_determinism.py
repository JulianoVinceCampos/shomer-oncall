"""Determinism contract: inputs idênticos -> serialização byte-idêntica."""

import hashlib
from datetime import date

import pytest

from shomer_oncall.adapters import json_writer
from shomer_oncall.config import AppConfig
from shomer_oncall.models import Location, Member, Observance, RestrictionKind, Team
from shomer_oncall.pipeline import build_schedule

pytestmark = pytest.mark.determinism

TEAM = Team(
    name="platform-sre",
    diaspora=True,
    members=(
        Member("rivka", Location("America/Sao_Paulo", -23.55, -46.63, 760),
               Observance(frozenset({RestrictionKind.SHABBAT, RestrictionKind.YOM_TOV}))),
        Member("dan", Location("Asia/Jerusalem", 31.78, 35.22, 754),
               Observance(frozenset({RestrictionKind.SHABBAT, RestrictionKind.YOM_TOV})),
               diaspora=False),
        Member("alex", Location("America/Sao_Paulo", -23.55, -46.63, 760)),
        Member("sam", Location("Europe/London", 51.51, -0.13, 35)),
    ),
)


def _serialize(bundle) -> str:
    return json_writer.dumps(json_writer.schedule_to_dict(bundle.schedule))


def test_byte_identical_across_runs():
    a = build_schedule(TEAM, date(2026, 1, 1), date(2026, 3, 31), AppConfig())
    b = build_schedule(TEAM, date(2026, 1, 1), date(2026, 3, 31), AppConfig())
    ha = hashlib.sha256(_serialize(a).encode()).hexdigest()
    hb = hashlib.sha256(_serialize(b).encode()).hexdigest()
    assert ha == hb


def test_member_order_does_not_change_output():
    reversed_team = Team(name=TEAM.name, diaspora=TEAM.diaspora,
                         members=tuple(reversed(TEAM.members)))
    a = build_schedule(TEAM, date(2026, 1, 1), date(2026, 2, 28), AppConfig())
    b = build_schedule(reversed_team, date(2026, 1, 1), date(2026, 2, 28), AppConfig())
    assert _serialize(a) == _serialize(b)
