"""Configuração de runtime: shift policy, load weights e gate thresholds.

Carregada de um arquivo TOML ou JSON (ambos stdlib), ou construída com defaults.
Todo threshold e weight vive aqui — nada é hard-coded na lógica
(docs/CLI.md#config-file, docs/METRICS.md#7).
"""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from .errors import ConfigError


class SchedulePolicy(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass(frozen=True, slots=True)
class Weights:
    base: float = 1.0
    weekend_mult: float = 2.0
    holiday_mult: float = 1.5
    night_mult: float = 1.25


@dataclass(frozen=True, slots=True)
class GateThresholds:
    jain_min: float = 0.95
    spread_max: float = 3.0
    equity_gap_max: float = 0.05


@dataclass(frozen=True, slots=True)
class AppConfig:
    policy: SchedulePolicy = SchedulePolicy.DAILY
    weights: Weights = Weights()
    gate: GateThresholds = GateThresholds()
    handoff_hour_local: int = 10  # hora local do handoff do shift


def _coerce(raw: dict[str, Any]) -> AppConfig:
    defaults = raw.get("defaults", {})
    weights = raw.get("weights", {})
    gate = raw.get("gate", {})
    try:
        policy = SchedulePolicy(defaults.get("policy", "daily"))
    except ValueError as exc:
        raise ConfigError(f"policy desconhecida: {defaults.get('policy')!r}") from exc
    return AppConfig(
        policy=policy,
        weights=Weights(
            base=float(weights.get("base", 1.0)),
            weekend_mult=float(weights.get("weekend_mult", 2.0)),
            holiday_mult=float(weights.get("holiday_mult", 1.5)),
            night_mult=float(weights.get("night_mult", 1.25)),
        ),
        gate=GateThresholds(
            jain_min=float(gate.get("jain_min", 0.95)),
            spread_max=float(gate.get("spread_max", 3.0)),
            equity_gap_max=float(gate.get("equity_gap_max", 0.05)),
        ),
        handoff_hour_local=int(defaults.get("handoff_hour_local", 10)),
    )


def load_config(path: str | Path | None) -> AppConfig:
    if path is None:
        return AppConfig()
    p = Path(path)
    if not p.exists():
        raise ConfigError(f"arquivo de config não encontrado: {p}")
    text = p.read_text(encoding="utf-8")
    try:
        raw = tomllib.loads(text) if p.suffix == ".toml" else json.loads(text)
    except (tomllib.TOMLDecodeError, json.JSONDecodeError) as exc:
        raise ConfigError(f"não foi possível parsear a config {p}: {exc}") from exc
    return _coerce(raw)
