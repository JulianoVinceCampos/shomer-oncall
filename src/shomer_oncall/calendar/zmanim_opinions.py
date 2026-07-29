"""Registry de opiniões de zmanim (shitot).

Cada opinião define como *tzais* (nightfall) é computado, mais uma citação. A
opinião é um parâmetro, nunca hard-coded downstream (docs/adr/0003). Este módulo é
o único lugar onde as opiniões vivem; o engine resolve um nome para uma Opinion e
a usa - sem branching por string em nenhum outro lugar.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..errors import UnknownShitahError


@dataclass(frozen=True, slots=True)
class Opinion:
    key: str
    # Exatamente uma das duas formas de definir tzais:
    depression_deg: float | None  # sol tantos graus abaixo do horizonte, ou
    fixed_minutes: float | None  # tantos minutos após o sunset
    citation: str
    # Minutos de fallback quando um tzais angular não tem solução (latitude alta).
    fallback_minutes: float = 72.0

    def is_angular(self) -> bool:
        return self.depression_deg is not None


_REGISTRY: dict[str, Opinion] = {
    op.key: op
    for op in (
        Opinion("gra_8.5", 8.5, None, "Escola do Vilna Gaon; default moderno comum"),
        Opinion("gra_16.1", 16.1, None, "GRA, stringent (~72 min no equinócio)"),
        Opinion("mga_16.1", None, 72.0, "Magen Avraham, fixed 72 minutos"),
        Opinion("fixed_40", None, 40.0, "Offset fixo de 40 minutos (comunitário)"),
        Opinion("rt_72", 16.1, None, "Rabbeinu Tam (72 min / 16.1 graus), mais stringent"),
    )
}

DEFAULT_SHITAH = "gra_8.5"


def get_opinion(key: str) -> Opinion:
    try:
        return _REGISTRY[key]
    except KeyError as exc:
        known = ", ".join(sorted(_REGISTRY))
        raise UnknownShitahError(f"shitah desconhecida {key!r}; conhecidas: {known}") from exc


def known_shitot() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))
