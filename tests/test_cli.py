"""Testes e2e da CLI: exit codes e artefatos de saída."""

import json
from pathlib import Path

from shomer_oncall.cli import main

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "team.json"


def test_schedule_e2e_pass(tmp_path):
    out = tmp_path / "s.ics"
    code = main([
        "schedule", "--team", str(EXAMPLE),
        "--from", "2026-01-01", "--to", "2026-03-31",
        "--out", str(out), "--gate",
    ])
    assert code == 0
    assert (tmp_path / "s.ics").exists()
    assert (tmp_path / "s.json").exists()
    metrics = json.loads((tmp_path / "s.metrics.json").read_text("utf-8"))
    assert metrics["coverage"]["violations"] == 0
    assert metrics["coverage"]["uncovered"] == 0
    assert metrics["fairness"]["jain"] >= 0.95


def test_ical_is_wellformed(tmp_path):
    out = tmp_path / "s.ics"
    main(["schedule", "--team", str(EXAMPLE), "--from", "2026-01-01",
          "--to", "2026-01-31", "--out", str(out)])
    text = (tmp_path / "s.ics").read_text("utf-8")
    assert text.startswith("BEGIN:VCALENDAR")
    assert text.strip().endswith("END:VCALENDAR")
    assert text.count("BEGIN:VEVENT") == text.count("END:VEVENT")


def test_explain_boundary(capsys):
    code = main(["explain-boundary", "--date", "2026-06-13",
                 "--location", "America/Sao_Paulo:-23.55:-46.63:760"])
    assert code == 0
    out = capsys.readouterr().out
    assert "shabbat" in out and "tzais" in out


def test_validate(capsys):
    code = main(["validate", "--team", str(EXAMPLE)])
    assert code == 0
    assert "platform-sre" in capsys.readouterr().out


def test_unknown_shitah_exit_5(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"members": [
        {"id": "a", "observes": ["shabbat"],
         "location": "Asia/Jerusalem:31.78:35.22:754", "shitah": "bogus"}]}), "utf-8")
    code = main(["schedule", "--team", str(bad), "--from", "2026-01-01",
                 "--to", "2026-01-07", "--out", str(tmp_path / "s.ics")])
    assert code == 5


def test_all_observant_uncovered_exit_3(tmp_path):
    team = tmp_path / "obs.json"
    team.write_text(json.dumps({"diaspora": True, "members": [
        {"id": "a", "observes": ["shabbat"], "location": "Asia/Jerusalem:31.78:35.22:754"},
        {"id": "b", "observes": ["shabbat"], "location": "Asia/Jerusalem:31.78:35.22:754"}]}),
        "utf-8")
    # Uma window contendo um sábado -> esse shift fica uncoverable num time all-observant.
    code = main(["schedule", "--team", str(team), "--from", "2026-01-01",
                 "--to", "2026-01-10", "--out", str(tmp_path / "s.ics")])
    assert code == 3
