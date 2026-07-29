"""Interface de linha de comando (argparse, apenas stdlib).

Subcomandos: schedule, explain-boundary, fairness, validate. Os exit codes seguem
docs/CLI.md#exit-codes. A CLI é o imperative shell: faz todo o I/O de arquivo e
console e traduz erros de domínio em exit codes.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import sys
from datetime import date, datetime
from pathlib import Path

from . import __version__
from .adapters import ical_writer, json_writer
from .adapters.team_loader import load_team, parse_location
from .calendar.engine import boundary_for
from .config import AppConfig, load_config
from .errors import ShomerError
from .models import Member, Observance, RestrictionKind
from .pipeline import build_schedule
from .reporting.audit import build_audit
from .reporting.metrics import CoverageMetrics, FairnessMetrics, compute_coverage, compute_fairness


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def _run_id(*parts: str) -> str:
    h = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return h[:12]


# --------------------------------------------------------------------------- #
# schedule
# --------------------------------------------------------------------------- #
def _load_history(path: str | None) -> dict[str, float]:
    if not path:
        return {}
    import json

    return {k: float(v) for k, v in json.loads(Path(path).read_text("utf-8")).items()}


def cmd_schedule(args: argparse.Namespace) -> int:
    team, observer_ids = load_team(args.team)
    config = load_config(args.config)
    ws, we = _parse_date(getattr(args, "from")), _parse_date(args.to)
    if we < ws:
        print("erro: --to é anterior a --from", file=sys.stderr)
        return 1

    bundle = build_schedule(team, ws, we, config, _load_history(args.history))
    sched = bundle.schedule
    loads = bundle.allocation.load_by_member
    uncovered = len(bundle.allocation.uncovered)
    violations = 1 if bundle.has_violation else 0

    fairness = compute_fairness(loads, observer_ids)
    coverage = compute_coverage(len(sched.shifts), uncovered, violations)
    run_id = _run_id(Path(args.team).read_text("utf-8"), getattr(args, "from"), args.to,
                     config.policy.value)

    out_base = Path(args.out)
    if out_base.parent and not out_base.parent.exists():
        out_base.parent.mkdir(parents=True, exist_ok=True)
    stem = out_base.with_suffix("")
    formats = {f.strip() for f in args.format.split(",")}
    written: list[str] = []
    if "ics" in formats:
        p = stem.with_suffix(".ics")
        p.write_text(ical_writer.to_ical(sched, run_id=run_id), encoding="utf-8", newline="")
        written.append(str(p))
    if "json" in formats:
        p = stem.with_suffix(".json")
        p.write_text(json_writer.dumps(json_writer.schedule_to_dict(sched)), encoding="utf-8")
        written.append(str(p))
    audit_path = stem.with_suffix(".audit.json")
    audit_path.write_text(
        json_writer.dumps({"run_id": run_id,
                           "records": build_audit(bundle.intervals_by_member, sched)}),
        encoding="utf-8",
    )
    metrics_doc = {
        "run_id": run_id,
        "window": {"from": ws.isoformat(), "to": we.isoformat(), "days": (we - ws).days + 1},
        "fairness": {
            "jain": fairness.jain, "gini": fairness.gini,
            "spread": fairness.spread, "equity_gap_pct": fairness.equity_gap_pct,
        },
        "coverage": {"ratio": coverage.ratio, "uncovered": coverage.uncovered,
                     "violations": coverage.violations},
    }
    metrics_path = stem.with_suffix(".metrics.json")
    metrics_path.write_text(json_writer.dumps(metrics_doc), encoding="utf-8")

    _print_scorecard(loads, observer_ids, fairness, coverage, ws, we)
    for w in [*written, str(audit_path), str(metrics_path)]:
        print(f"  gravado {w}")

    if violations:
        print("FALHA: hard violation detectada (bug)", file=sys.stderr)
        return 2
    if uncovered:
        print(f"FALHA: {uncovered} shift(s) uncovered", file=sys.stderr)
        return 3
    if args.gate and not _fairness_ok(fairness, config):
        print("FALHA: fairness abaixo dos thresholds configurados", file=sys.stderr)
        return 4
    return 0


def _fairness_ok(fairness: FairnessMetrics, config: AppConfig) -> bool:
    g = config.gate
    return (
        fairness.jain >= g.jain_min
        and fairness.spread <= g.spread_max
        and fairness.equity_gap_pct / 100.0 <= g.equity_gap_max
    )


def _print_scorecard(
    loads: dict[str, float],
    observer_ids: set[str],
    fairness: FairnessMetrics,
    coverage: CoverageMetrics,
    ws: date,
    we: date,
) -> None:
    total = sum(loads.values())
    n = len(loads) or 1
    equal = total / n
    days = (we - ws).days + 1
    print(f"Relatório de fairness de plantão  ·  window: {ws} -> {we} ({days}d)")
    print("-" * 62)
    print(f"{'membro':10s} {'weighted load':>14s} {'share':>8s} {'Δ vs igual':>12s}")
    for mid in sorted(loads):
        load = loads[mid]
        share = (load / total * 100) if total else 0.0
        delta = (load - equal) / equal * 100 if equal else 0.0
        tag = " *" if mid in observer_ids else ""
        print(f"{mid + tag:10s} {load:>14.2f} {share:>7.1f}% {delta:>+11.1f}%")
    print("-" * 62)
    print(f"Jain fairness index      : {fairness.jain:.3f}")
    print(f"Gini coefficient         : {fairness.gini:.3f}")
    print(f"Weighted spread          : {fairness.spread:.2f}")
    print(f"Gap observer/non-observer: {fairness.equity_gap_pct:.2f}%")
    print(f"Coverage                 : {coverage.ratio * 100:.0f}%  ·  "
          f"violations: {coverage.violations}")
    print(f"Shifts uncovered         : {coverage.uncovered}")
    print("(* = membro observante)")


# --------------------------------------------------------------------------- #
# explain-boundary
# --------------------------------------------------------------------------- #
def cmd_explain_boundary(args: argparse.Namespace) -> int:
    loc = parse_location(args.location)
    categories = frozenset({RestrictionKind.SHABBAT, RestrictionKind.YOM_TOV})
    member = Member(
        id="_probe",
        location=loc,
        observance=Observance(categories, candle_buffer_min=args.buffer, shitah=args.shitah),
        diaspora=not args.israel,
    )
    d = _parse_date(args.date)
    iv = boundary_for(d, member, diaspora=not args.israel)
    if iv is None:
        print(f"{args.date}: não é um dia restrito para shabbat/yom_tov nesta location.")
        return 0
    r = iv.rationale
    print(f"{iv.kind.value}  ·  {args.date}  ·  {loc.timezone} "
          f"(lat {loc.latitude}, lon {loc.longitude}, {loc.elevation_m:g} m)")
    print(f"  inicia  {iv.start_utc.isoformat()}   (shkiah da véspera {r['start']['eve']} "
          f"- {r['start']['buffer_min']} min de buffer)")
    end = r["end"]
    how = (f"{end['depression_deg']} graus de depression" if end["depression_deg"] is not None
           else f"{end['fixed_minutes']} min após o sunset")
    print(f"  termina {iv.end_utc.isoformat()}   (tzais, {end['shitah']}: {how})")
    print(f"  fallback: {'sim' if end['fallback'] else 'não'}")
    return 0


# --------------------------------------------------------------------------- #
# fairness (pontua um schedule.json existente)
# --------------------------------------------------------------------------- #
def cmd_fairness(args: argparse.Namespace) -> int:
    import json

    doc = json.loads(Path(args.schedule).read_text("utf-8"))
    weight_by_shift = {s["id"]: s["weight"] for s in doc["shifts"]}
    loads: dict[str, float] = {}
    for a in doc["assignments"]:
        if a["member"] is None:
            continue
        loads[a["member"]] = loads.get(a["member"], 0.0) + weight_by_shift[a["shift"]]
    observer_ids: set[str] = set()
    if args.team:
        _, observer_ids = load_team(args.team)
    config = load_config(args.config)
    fairness = compute_fairness({k: round(v, 6) for k, v in loads.items()}, observer_ids)
    uncovered = sum(1 for a in doc["assignments"] if a["member"] is None)
    coverage = compute_coverage(len(doc["shifts"]), uncovered, 0)
    ws = _parse_date(doc["window"]["from"])
    we = _parse_date(doc["window"]["to"])
    _print_scorecard(loads, observer_ids, fairness, coverage, ws, we)
    if args.gate and not _fairness_ok(fairness, config):
        return 4
    return 0


# --------------------------------------------------------------------------- #
# validate
# --------------------------------------------------------------------------- #
def cmd_validate(args: argparse.Namespace) -> int:
    team, observer_ids = load_team(args.team)
    print(f"OK: time '{team.name}' com {len(team.members)} membro(s); "
          f"{len(observer_ids)} observante(s).")
    if observer_ids and len(observer_ids) == len(team.members):
        print("AVISO: todos os membros são observantes; períodos de Yom Tov de vários "
              "dias podem ficar uncoverable dentro do time.", file=sys.stderr)
    return 0


# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="shomer-oncall",
                                description="Rotação de plantão (on-call) justa e "
                                "ciente do calendário hebraico.")
    p.add_argument("--version", action="version", version=f"shomer-oncall {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("schedule", help="gera uma rotação")
    s.add_argument("--team", required=True)
    s.add_argument("--from", required=True, dest="from")
    s.add_argument("--to", required=True)
    s.add_argument("--out", default="schedule.ics")
    s.add_argument("--format", default="ics,json")
    s.add_argument("--config", default=None)
    s.add_argument("--history", default=None)
    s.add_argument("--gate", action="store_true")
    s.set_defaults(func=cmd_schedule)

    e = sub.add_parser("explain-boundary", help="explica um boundary de Shabbat/Yom Tov")
    e.add_argument("--date", required=True)
    e.add_argument("--location", required=True)
    e.add_argument("--shitah", default="gra_8.5")
    e.add_argument("--buffer", type=int, default=18)
    e.add_argument("--israel", action="store_true", help="Yom Tov de um dia (default: diaspora)")
    e.set_defaults(func=cmd_explain_boundary)

    f = sub.add_parser("fairness", help="pontua um schedule.json existente")
    f.add_argument("--schedule", required=True)
    f.add_argument("--team", default=None)
    f.add_argument("--config", default=None)
    f.add_argument("--gate", action="store_true")
    f.set_defaults(func=cmd_fairness)

    v = sub.add_parser("validate", help="checagem estática de um arquivo de time")
    v.add_argument("--team", required=True)
    v.set_defaults(func=cmd_validate)
    return p


def main(argv: list[str] | None = None) -> int:
    # Garante saída UTF-8 no console (Windows usa cp1252 por padrão, que não
    # encoda caracteres como Δ nem acentos PT-BR). Ignorado se o stream não suporta.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            with contextlib.suppress(ValueError, OSError):
                reconfigure(encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        exit_code: int = args.func(args)
        return exit_code
    except ShomerError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
