"""Golden anchors do calendário hebraico contra datas bem estabelecidas."""

import pytest

from shomer_oncall.calendar import hebrew as H

pytestmark = pytest.mark.golden

# (hebrew_year, month, day) -> Gregoriano autoritativo (year, month, day).
# Numeração de mês: Nisan=1, Sivan=3, Tishri=7.
ANCHORS = [
    ((5784, 7, 1), (2023, 9, 16)),   # Rosh Hashanah 5784
    ((5784, 7, 10), (2023, 9, 25)),  # Yom Kippur 5784
    ((5784, 1, 15), (2024, 4, 23)),  # 1o dia de Pesach 5784
    ((5784, 3, 6), (2024, 6, 12)),   # Shavuot 5784
    ((5785, 7, 1), (2024, 10, 3)),   # Rosh Hashanah 5785
    ((5786, 7, 1), (2025, 9, 23)),   # Rosh Hashanah 5786
]


@pytest.mark.parametrize("hebrew,gregorian", ANCHORS)
def test_hebrew_to_gregorian(hebrew, gregorian):
    assert H.gregorian_from_fixed(H.fixed_from_hebrew(*hebrew)) == gregorian


@pytest.mark.parametrize("hebrew,gregorian", ANCHORS)
def test_roundtrip_hebrew(hebrew, gregorian):
    fixed = H.fixed_from_gregorian(*gregorian)
    assert H.hebrew_from_fixed(fixed) == hebrew


def test_gregorian_roundtrip_range():
    base = H.fixed_from_gregorian(2020, 1, 1)
    for offset in range(0, 4000, 7):
        f = base + offset
        assert H.fixed_from_gregorian(*H.gregorian_from_fixed(f)) == f


def test_leap_year_cycle():
    # 7 anos bissextos por ciclo de 19 anos.
    leaps = sum(1 for y in range(5784, 5784 + 19) if H.hebrew_leap_year(y))
    assert leaps == 7


def test_year_lengths_are_valid():
    for y in range(5780, 5800):
        assert H.days_in_hebrew_year(y) in (353, 354, 355, 383, 384, 385)
