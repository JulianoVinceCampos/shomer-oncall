"""Fórmulas de métricas contra valores calculados à mão."""

import math

from shomer_oncall.reporting import metrics as M


def test_jain_perfect_equality():
    assert M.jain_index([5, 5, 5, 5]) == 1.0


def test_jain_all_zero_is_fair():
    assert M.jain_index([0, 0, 0]) == 1.0


def test_jain_known_value():
    # loads [1,3]: (4)^2 / (2*(1+9)) = 16/20 = 0.8
    assert math.isclose(M.jain_index([1, 3]), 0.8)


def test_gini_equality_is_zero():
    assert M.gini_coefficient([7, 7, 7]) == 0.0


def test_gini_known_value():
    # loads [0, 10]: soma|diff| = 20; /(2*2*10) = 0.5
    assert math.isclose(M.gini_coefficient([0, 10]), 0.5)


def test_spread():
    assert M.weighted_spread([2.0, 5.5, 3.0]) == 3.5
    assert M.weighted_spread([]) == 0.0


def test_equity_gap_zero_when_balanced():
    gap, pct = M.equity_gap({"a": 10, "b": 10, "c": 10, "d": 10}, {"a", "b"})
    assert gap == 0.0 and pct == 0.0


def test_equity_gap_detects_imbalance():
    # observers carregam 4 cada, non-observers 8 cada -> gap 4.
    gap, pct = M.equity_gap({"o1": 4, "o2": 4, "n1": 8, "n2": 8}, {"o1", "o2"})
    assert gap == 4.0
    assert pct > 0


def test_equity_gap_zero_when_one_group_empty():
    gap, pct = M.equity_gap({"a": 3, "b": 9}, set())
    assert gap == 0.0 and pct == 0.0


def test_coverage():
    cov = M.compute_coverage(total_shifts=90, uncovered=0, violations=0)
    assert cov.ratio == 1.0 and cov.uncovered == 0
    cov2 = M.compute_coverage(total_shifts=10, uncovered=2, violations=0)
    assert cov2.ratio == 0.8
