"""Classificação de holidays e a regra de dois dias na diaspora."""

from shomer_oncall.calendar import hebrew as H
from shomer_oncall.calendar import holidays
from shomer_oncall.models import RestrictionKind

YOM_TOV = frozenset({RestrictionKind.YOM_TOV})


def test_diaspora_has_more_yom_tov_days_than_israel():
    israel = holidays.yom_tov_days(5786, diaspora=False)
    diaspora = holidays.yom_tov_days(5786, diaspora=True)
    assert len(diaspora) > len(israel)


def test_rosh_hashanah_is_two_days_everywhere():
    for diaspora in (True, False):
        days = holidays.yom_tov_days(5786, diaspora)
        rh1 = H.fixed_from_hebrew(5786, 7, 1)
        rh2 = H.fixed_from_hebrew(5786, 7, 2)
        assert rh1 in days and rh2 in days


def test_shavuot_second_day_only_in_diaspora():
    second = H.fixed_from_hebrew(5786, 3, 7)
    assert second in holidays.yom_tov_days(5786, diaspora=True)
    assert second not in holidays.yom_tov_days(5786, diaspora=False)


def test_restricted_days_only_includes_requested_categories():
    only_yt = holidays.restricted_days(5786, True, YOM_TOV)
    assert all(k is RestrictionKind.YOM_TOV for k in only_yt.values())
    with_fasts = holidays.restricted_days(
        5786, True, frozenset({RestrictionKind.YOM_TOV, RestrictionKind.FAST})
    )
    assert any(k is RestrictionKind.FAST for k in with_fasts.values())
