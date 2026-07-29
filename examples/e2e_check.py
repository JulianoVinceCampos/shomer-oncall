#!/usr/bin/env python3
"""Verificador end-to-end (smoke-test) do shomer-oncall.

Roda o fluxo completo pela API publica sobre o time de exemplo, AFIRMA as garantias
do dominio e escreve um relatorio estruturado. Sai com codigo 0 se tudo passa, 1 caso
contrario -- serve tanto para conferir localmente quanto como smoke-test de CI.

Uso:
    PYTHONPATH=src python examples/e2e_check.py [--out CAMINHO_RELATORIO]

Garantias verificadas:
  1. Zero hard violations (nenhum observante paginado em restricted interval).
  2. Cobertura total (nenhum shift uncovered).
  3. Gate de fairness: Jain >= 0.95, weighted spread <= 3.0, equity gap <= 5%.
  4. Prova do dominio: zero shifts de sexta/sabado atribuidos a observantes.
  5. Determinismo: duas execucoes produzem a mesma serializacao.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from shomer_oncall.adapters import json_writer  # noqa: E402
from shomer_oncall.adapters.team_loader import load_team  # noqa: E402
from shomer_oncall.config import AppConfig  # noqa: E402
from shomer_oncall.pipeline import build_schedule  # noqa: E402
from shomer_oncall.reporting.metrics import compute_fairness  # noqa: E402

WINDOW_START = date(2026, 7, 1)
WINDOW_END = date(2026, 9, 30)
DIAS = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]


def run(team_path: Path) -> tuple[list[str], bool]:
    team, observer_ids = load_team(team_path)
    cfg = AppConfig()
    bundle = build_schedule(team, WINDOW_START, WINDOW_END, cfg)
    loads = bundle.allocation.load_by_member
    fairness = compute_fairness(loads, observer_ids)

    # Contagem de shifts + deteccao de sexta/sabado para observantes.
    shifts_by_member: dict[str, int] = dict.fromkeys(loads, 0)
    weekend_para_observante = 0
    shift_by_id = {s.id: s for s in bundle.schedule.shifts}
    for a in bundle.schedule.assignments:
        if a.member_id is None:
            continue
        shifts_by_member[a.member_id] += 1
        weekday = shift_by_id[a.shift_id].start_utc.weekday()
        if a.member_id in observer_ids and weekday in (4, 5):
            weekend_para_observante += 1

    # Determinismo: recompoe e compara a serializacao.
    ser1 = json_writer.dumps(json_writer.schedule_to_dict(bundle.schedule))
    bundle2 = build_schedule(team, WINDOW_START, WINDOW_END, cfg)
    ser2 = json_writer.dumps(json_writer.schedule_to_dict(bundle2.schedule))

    checks = [
        ("Zero hard violations", not bundle.has_violation),
        ("Cobertura total (0 uncovered)", not bundle.allocation.uncovered),
        ("Jain >= 0.95", fairness.jain >= 0.95),
        ("Weighted spread <= 3.0", fairness.spread <= 3.0),
        ("Equity gap <= 5%", fairness.equity_gap_pct <= 5.0),
        ("Zero sexta/sabado para observantes", weekend_para_observante == 0),
        ("Determinismo (serializacao identica)", ser1 == ser2),
    ]

    total = sum(loads.values())
    n = len(loads) or 1
    equal = total / n
    days = (WINDOW_END - WINDOW_START).days + 1

    out: list[str] = []
    out.append("=" * 64)
    out.append(f"shomer-oncall :: verificacao end-to-end ({team.name})")
    out.append(f"window: {WINDOW_START} -> {WINDOW_END} ({days}d) | "
               f"{len(bundle.schedule.shifts)} shifts | observantes: {sorted(observer_ids)}")
    out.append("=" * 64)
    out.append(f"{'membro':10s} {'obs':4s} {'shifts':>7s} {'weighted_load':>14s} {'delta':>9s}")
    for mid in sorted(loads):
        tag = "sim" if mid in observer_ids else "-"
        d = (loads[mid] - equal) / equal * 100 if equal else 0.0
        out.append(f"{mid:10s} {tag:4s} {shifts_by_member[mid]:>7d} "
                   f"{loads[mid]:>14.2f} {d:>+8.1f}%")
    out.append("-" * 64)
    out.append(f"Jain={fairness.jain:.4f} | Gini={fairness.gini:.4f} | "
               f"spread={fairness.spread:.2f} | equity_gap={fairness.equity_gap_pct:.2f}%")
    out.append("-" * 64)
    ok = True
    for nome, passou in checks:
        ok = ok and passou
        out.append(f"  [{'PASS' if passou else 'FAIL'}] {nome}")
    out.append("=" * 64)
    out.append("RESULTADO: " + ("TODOS OS CHECKS PASSARAM" if ok else "FALHA"))
    return out, ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke-test end-to-end do shomer-oncall")
    parser.add_argument("--team", default=str(ROOT / "examples" / "team.json"))
    parser.add_argument("--out", default=None, help="grava o relatorio neste caminho")
    args = parser.parse_args(argv)

    lines, ok = run(Path(args.team))
    report = "\n".join(lines) + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(report, encoding="utf-8")
    print(report)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
