"""Cobertura adicional: clock, weekly shifts, weights, chol hamoed, paths da CLI."""

import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from shomer_oncall.calendar import holidays
from shomer_oncall.cli import main
from shomer_oncall.clock import FixedClock, SystemClock
from shomer_oncall.config import SchedulePolicy, Weights
from shomer_oncall.models import RestrictionKind
from shomer_oncall.scheduling.generator import generate_shifts
from shomer_oncall.scheduling.weights import day_weight

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "team.json"


# --- clock ---
def test_fixed_clock_returns_instant():
    inst = datetime(2026, 1, 1, 12, tzinfo=UTC)
    assert FixedClock(inst).now() == inst


def test_fixed_clock_rejects_naive():
    with pytest.raises(ValueError):
        FixedClock(datetime(2026, 1, 1, 12))


def test_system_clock_is_tz_aware():
    assert SystemClock().now().tzinfo is not None


# --- weekly generator ---
def test_weekly_shifts_count_and_weight():
    shifts = generate_shifts(date(2026, 1, 1), date(2026, 1, 28),
                             SchedulePolicy.WEEKLY, Weights(), handoff_hour=10)
    assert len(shifts) == 4
    # o weight semanal é a soma dos 7 daily weights, logo > 7 * base com weekends.
    assert all(s.weight > 7.0 for s in shifts)
    assert all(s.id.startswith("week-") for s in shifts)


# --- weights ---
def test_holiday_multiplier_applies():
    weekday = datetime(2026, 1, 6, 10, tzinfo=UTC)  # uma terça-feira
    w_plain, basis_plain = day_weight(weekday, Weights(), frozenset())
    w_holiday, basis_holiday = day_weight(weekday, Weights(), frozenset({date(2026, 1, 6)}))
    assert w_holiday > w_plain
    assert "holiday" in basis_holiday and "holiday" not in basis_plain


# --- chol hamoed ---
def test_chol_hamoed_category_produces_intermediate_days():
    r = holidays.restricted_days(5786, True, frozenset({RestrictionKind.CHOL_HAMOED}))
    assert any(k is RestrictionKind.CHOL_HAMOED for k in r.values())


# --- CLI: fairness + history + explain israel + data não-restrita ---
def test_cli_fairness_command(tmp_path, capsys):
    out = tmp_path / "s.ics"
    main(["schedule", "--team", str(EXAMPLE), "--from", "2026-01-01",
          "--to", "2026-02-28", "--out", str(out)])
    code = main(["fairness", "--schedule", str(tmp_path / "s.json"),
                 "--team", str(EXAMPLE), "--gate"])
    assert code == 0
    assert "Jain fairness index" in capsys.readouterr().out


def test_cli_schedule_with_history(tmp_path):
    hist = tmp_path / "h.json"
    hist.write_text(json.dumps({"alex": 50.0}), "utf-8")
    code = main(["schedule", "--team", str(EXAMPLE), "--from", "2026-01-01",
                 "--to", "2026-01-31", "--out", str(tmp_path / "s.ics"),
                 "--history", str(hist)])
    assert code == 0
    metrics = json.loads((tmp_path / "s.metrics.json").read_text("utf-8"))
    assert metrics["run_id"]


def test_cli_explain_israel_one_day(capsys):
    code = main(["explain-boundary", "--date", "2026-05-22",
                 "--location", "Asia/Jerusalem:31.78:35.22:754", "--israel"])
    assert code == 0


def test_cli_explain_non_restricted_date(capsys):
    # Uma quarta-feira, não é Shabbat/Yom Tov.
    code = main(["explain-boundary", "--date", "2026-06-10",
                 "--location", "America/Sao_Paulo:-23.55:-46.63:760"])
    assert code == 0
    assert "não é um dia restrito" in capsys.readouterr().out


def test_cli_to_before_from(tmp_path):
    code = main(["schedule", "--team", str(EXAMPLE), "--from", "2026-03-01",
                 "--to", "2026-01-01", "--out", str(tmp_path / "s.ics")])
    assert code == 1
