"""Validação do team loader e carregamento de config."""

import json

import pytest

from shomer_oncall.adapters.team_loader import load_team, parse_location
from shomer_oncall.config import SchedulePolicy, load_config
from shomer_oncall.errors import ConfigError, InvalidTeamError, UnknownShitahError


def _write(tmp_path, name, obj):
    p = tmp_path / name
    p.write_text(json.dumps(obj), encoding="utf-8")
    return p


def test_parse_location_ok():
    loc = parse_location("America/Sao_Paulo:-23.55:-46.63:760")
    assert loc.latitude == -23.55 and loc.elevation_m == 760


def test_parse_location_bad_format():
    with pytest.raises(InvalidTeamError):
        parse_location("sem-dois-pontos")


def test_load_team_ok(tmp_path):
    p = _write(tmp_path, "t.json", {
        "team": "x", "diaspora": True,
        "members": [
            {"id": "a", "observes": ["shabbat"], "location": "Asia/Jerusalem:31.78:35.22:754"},
            {"id": "b", "observes": [], "location": "Europe/London:51.51:-0.13:35"},
        ],
    })
    team, observers = load_team(p)
    assert len(team.members) == 2
    assert observers == {"a"}


def test_unknown_shitah_rejected(tmp_path):
    p = _write(tmp_path, "t.json", {
        "members": [{"id": "a", "observes": ["shabbat"],
                     "location": "Asia/Jerusalem:31.78:35.22:754", "shitah": "nope"}]
    })
    with pytest.raises(UnknownShitahError):
        load_team(p)


def test_unknown_category_rejected(tmp_path):
    p = _write(tmp_path, "t.json", {
        "members": [{"id": "a", "observes": ["natal"],
                     "location": "Asia/Jerusalem:31.78:35.22:754"}]
    })
    with pytest.raises(InvalidTeamError):
        load_team(p)


def test_duplicate_id_rejected(tmp_path):
    p = _write(tmp_path, "t.json", {
        "members": [
            {"id": "a", "observes": [], "location": "Europe/London:51.51:-0.13:35"},
            {"id": "a", "observes": [], "location": "Europe/London:51.51:-0.13:35"},
        ]
    })
    with pytest.raises(InvalidTeamError):
        load_team(p)


def test_default_config():
    cfg = load_config(None)
    assert cfg.policy is SchedulePolicy.DAILY
    assert cfg.weights.weekend_mult == 2.0


def test_config_from_toml(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text("[weights]\nweekend_mult = 3.0\n", encoding="utf-8")
    cfg = load_config(p)
    assert cfg.weights.weekend_mult == 3.0


def test_missing_config_raises():
    with pytest.raises(ConfigError):
        load_config("nao-existe.toml")
