"""Allocator: coverage, respeito à feasibility, fairness vs baseline, determinismo."""

from datetime import UTC, datetime, timedelta

from shomer_oncall.models import Shift
from shomer_oncall.reporting.metrics import jain_index
from shomer_oncall.scheduling.allocator import allocate


def _shifts(n, weekend_every=7):
    base = datetime(2026, 1, 1, 10, tzinfo=UTC)
    out = []
    for i in range(n):
        w = 2.0 if i % weekend_every in (5, 6) else 1.0
        out.append(Shift(id=f"{i:03d}", start_utc=base + timedelta(days=i),
                         end_utc=base + timedelta(days=i + 1), weight=w))
    return out


def test_every_shift_assigned_when_feasible():
    shifts = _shifts(20)
    members = ["a", "b", "c"]
    feasible = {s.id: list(members) for s in shifts}
    res = allocate(shifts, feasible, members)
    assigned = [a for a in res.assignments if a.member_id is not None]
    assert len(assigned) == 20
    assert not res.uncovered


def test_respects_feasibility():
    shifts = _shifts(10)
    # 'a' não pode pegar o primeiro shift.
    feasible = {s.id: ["a", "b"] for s in shifts}
    feasible["000"] = ["b"]
    res = allocate(shifts, feasible, ["a", "b"])
    first = next(a for a in res.assignments if a.shift_id == "000")
    assert first.member_id == "b"


def test_uncovered_when_no_candidates():
    shifts = _shifts(5)
    feasible = {s.id: ["a"] for s in shifts}
    feasible["002"] = []
    res = allocate(shifts, feasible, ["a"])
    assert "002" in res.uncovered


def test_fairness_not_worse_than_round_robin():
    shifts = _shifts(30)
    members = ["a", "b", "c"]
    feasible = {s.id: list(members) for s in shifts}
    res = allocate(shifts, feasible, members)
    alloc_jain = jain_index(list(res.load_by_member.values()))

    # Baseline de load por round-robin.
    rr = dict.fromkeys(members, 0.0)
    for i, s in enumerate(shifts):
        rr[members[i % 3]] += s.weight
    assert alloc_jain >= jain_index(list(rr.values())) - 1e-9


def test_deterministic():
    shifts = _shifts(25)
    members = ["a", "b", "c", "d"]
    feasible = {s.id: list(members) for s in shifts}
    r1 = allocate(shifts, feasible, members)
    r2 = allocate(shifts, feasible, members)
    assert r1.assignments == r2.assignments
    assert r1.load_by_member == r2.load_by_member


def test_history_carry_in_biases_away_from_loaded_member():
    shifts = _shifts(4, weekend_every=99)  # todos com weight igual
    members = ["a", "b"]
    feasible = {s.id: list(members) for s in shifts}
    res = allocate(shifts, feasible, members, history={"a": 100.0})
    # 'a' começa muito carregado, então 'b' deve pegar os shifts.
    assert res.load_by_member["b"] > 0
    assert res.load_by_member["a"] == 100.0
