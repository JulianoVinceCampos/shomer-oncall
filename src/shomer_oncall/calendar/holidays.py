"""Classificação de dias do calendário hebraico em restricted categories.

Dado um ano hebraico, produz o conjunto de dias restritos (como datas fixas RD)
com o seu kind, honrando a regra de festival de dois dias na diaspora. Festivais
que não têm restrição de trabalho (Purim, Chanukah) estão ausentes de propósito -
nunca bloqueiam o plantão (docs/DOMAIN.md#3).

Números de mês: Nisan=1, Sivan=3, Av=5, Tishri=7 (ver hebrew.py).
"""

from __future__ import annotations

from ..models import RestrictionKind
from .hebrew import fixed_from_hebrew

# Âncoras (mês, dia) dentro do ano hebraico.
_TISHRI, _NISAN, _SIVAN, _AV = 7, 1, 3, 5


def _rd(year: int, month: int, day: int) -> int:
    return fixed_from_hebrew(year, month, day)


def yom_tov_days(hebrew_year: int, diaspora: bool) -> dict[int, RestrictionKind]:
    """RD -> kind para todos os dias de festival com restrição de trabalho do ano."""
    out: dict[int, RestrictionKind] = {}

    def add(rd: int, kind: RestrictionKind = RestrictionKind.YOM_TOV) -> None:
        out[rd] = kind

    # Rosh Hashanah: 1-2 Tishri (dois dias em todo lugar).
    add(_rd(hebrew_year, _TISHRI, 1))
    add(_rd(hebrew_year, _TISHRI, 2))
    # Yom Kippur: 10 Tishri.
    add(_rd(hebrew_year, _TISHRI, 10))
    # Sukkot dia 1 (+ dia 2 na diaspora): 15 (,16) Tishri.
    add(_rd(hebrew_year, _TISHRI, 15))
    if diaspora:
        add(_rd(hebrew_year, _TISHRI, 16))
    # Shemini Atzeret 22 Tishri (+ Simchat Torah 23 na diaspora).
    add(_rd(hebrew_year, _TISHRI, 22))
    if diaspora:
        add(_rd(hebrew_year, _TISHRI, 23))
    # Pesach: 15 & 21 Nisan (Israel); 15,16,21,22 (diaspora).
    add(_rd(hebrew_year, _NISAN, 15))
    add(_rd(hebrew_year, _NISAN, 21))
    if diaspora:
        add(_rd(hebrew_year, _NISAN, 16))
        add(_rd(hebrew_year, _NISAN, 22))
    # Shavuot: 6 Sivan (+ 7 na diaspora).
    add(_rd(hebrew_year, _SIVAN, 6))
    if diaspora:
        add(_rd(hebrew_year, _SIVAN, 7))
    return out


def chol_hamoed_days(hebrew_year: int, diaspora: bool) -> set[int]:
    """Dias intermediários de festival (restrição opt-in)."""
    days: set[int] = set()
    # Sukkot: 17-21 Tishri (diaspora), 16-21 (Israel). Dia 22 é Shemini Atzeret.
    sukkot_start = 17 if diaspora else 16
    for d in range(sukkot_start, 22):
        days.add(_rd(hebrew_year, _TISHRI, d))
    # Pesach: 17-20 Nisan (diaspora), 16-20 (Israel).
    pesach_start = 17 if diaspora else 16
    for d in range(pesach_start, 21):
        days.add(_rd(hebrew_year, _NISAN, d))
    return days


def fast_days(hebrew_year: int) -> set[int]:
    """Fast days maiores onde atuar num page é geralmente permitido (soft; opt-in).
    Yom Kippur é excluído aqui porque já é Yom Tov (hard block)."""
    days: set[int] = set()
    days.add(_rd(hebrew_year, _AV, 9))  # Tisha B'Av
    return days


def restricted_days(
    hebrew_year: int,
    diaspora: bool,
    categories: frozenset[RestrictionKind],
) -> dict[int, RestrictionKind]:
    """Mapa combinado RD -> kind para as categorias pedidas (Shabbat é tratado à
    parte no engine, por ser semanal e não calendar-anchored)."""
    out: dict[int, RestrictionKind] = {}
    if RestrictionKind.YOM_TOV in categories:
        out.update(yom_tov_days(hebrew_year, diaspora))
    if RestrictionKind.CHOL_HAMOED in categories:
        for rd in chol_hamoed_days(hebrew_year, diaspora):
            out.setdefault(rd, RestrictionKind.CHOL_HAMOED)
    if RestrictionKind.FAST in categories:
        for rd in fast_days(hebrew_year):
            out.setdefault(rd, RestrictionKind.FAST)
    return out
