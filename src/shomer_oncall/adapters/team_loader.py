"""Carrega e valida a definição de time a partir de JSON (ou YAML se PyYAML existir).

JSON é o default zero-dependency. O formato da string de location é
"TZ:lat:lon:elevation_m" (docs/CLI.md#location-syntax). A validação é estrita:
categorias desconhecidas, coordenadas inválidas e shitot desconhecidas são
rejeitadas antes de qualquer scheduling (mapeando para o exit code 5).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..calendar.zmanim_opinions import DEFAULT_SHITAH, get_opinion
from ..errors import InvalidTeamError
from ..models import Location, Member, Observance, RestrictionKind, Team


def parse_location(spec: str) -> Location:
    parts = spec.split(":")
    if len(parts) != 4:
        raise InvalidTeamError(
            f"location deve ser 'TZ:lat:lon:elevation_m', recebido {spec!r}"
        )
    tz, lat, lon, elev = parts
    try:
        loc = Location(tz, float(lat), float(lon), float(elev))
    except ValueError as exc:
        raise InvalidTeamError(f"location inválida {spec!r}: {exc}") from exc
    return loc


def _parse_categories(raw: list[str]) -> frozenset[RestrictionKind]:
    out: set[RestrictionKind] = set()
    for item in raw:
        try:
            out.add(RestrictionKind(item))
        except ValueError as exc:
            valid = ", ".join(k.value for k in RestrictionKind)
            raise InvalidTeamError(
                f"categoria de observance desconhecida {item!r}; válidas: {valid}"
            ) from exc
    return frozenset(out)


def _load_raw(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore[import-untyped]
        except ModuleNotFoundError as exc:
            raise InvalidTeamError(
                "arquivos YAML de time exigem PyYAML; use JSON ou `pip install pyyaml`"
            ) from exc
        return dict(yaml.safe_load(text))
    return dict(json.loads(text))


def load_team(path: str | Path) -> tuple[Team, set[str]]:
    """Retorna (Team, observer_ids)."""
    p = Path(path)
    if not p.exists():
        raise InvalidTeamError(f"arquivo de time não encontrado: {p}")
    try:
        raw = _load_raw(p)
    except (json.JSONDecodeError, ValueError) as exc:
        raise InvalidTeamError(f"não foi possível parsear o arquivo de time {p}: {exc}") from exc

    if not isinstance(raw, dict) or "members" not in raw:
        raise InvalidTeamError("o arquivo de time deve ser um objeto com uma lista 'members'")

    name = raw.get("team", "team")
    diaspora = bool(raw.get("diaspora", True))
    members: list[Member] = []
    observer_ids: set[str] = set()
    seen: set[str] = set()

    for entry in raw["members"]:
        mid = entry.get("id")
        if not mid:
            raise InvalidTeamError("todo membro precisa de um 'id'")
        if mid in seen:
            raise InvalidTeamError(f"id de membro duplicado: {mid!r}")
        seen.add(mid)
        location = parse_location(entry["location"])
        categories = _parse_categories(entry.get("observes", []))
        observance = None
        if categories:
            shitah = entry.get("shitah", DEFAULT_SHITAH)
            get_opinion(shitah)  # valida; levanta UnknownShitahError (exit 5)
            observance = Observance(
                categories=categories,
                candle_buffer_min=int(entry.get("candle_buffer_min", 18)),
                shitah=shitah,
            )
            observer_ids.add(mid)
        members.append(
            Member(
                id=mid,
                location=location,
                observance=observance,
                diaspora=entry.get("diaspora"),
            )
        )

    if not members:
        raise InvalidTeamError("o time não tem membros")

    return Team(name=name, members=tuple(members), diaspora=diaspora), observer_ids
