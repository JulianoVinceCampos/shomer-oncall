"""Aritmética do calendário hebraico (Hillel), a partir dos primeiros princípios.

Implementa a representação em dia fixo ("Rata Die", RD) e as conversões entre o
calendário gregoriano proléptico e o calendário hebraico aritmético, seguindo os
algoritmos de Dershowitz & Reingold, *Calendrical Calculations*. Sem dependências
de terceiros — este é o calendar authority em que o resto do sistema confia, e é
validado contra anchors conhecidas na golden test suite.

Numeração dos meses (hebraico): Nisan=1, Iyar=2, Sivan=3, Tammuz=4, Av=5, Elul=6,
Tishri=7, Marheshvan=8, Kislev=9, Tevet=10, Shevat=11, Adar(I)=12, Adar II=13.
O ano civil começa em Tishri (mês 7).
"""

from __future__ import annotations

from datetime import date as _date

# Dia fixo (RD) de 1 Tishri, ano hebraico 1.
HEBREW_EPOCH = -1373427


# --------------------------------------------------------------------------- #
# Gregoriano <-> fixed
# --------------------------------------------------------------------------- #
def gregorian_is_leap(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def fixed_from_gregorian(year: int, month: int, day: int) -> int:
    """Número do dia RD para uma data gregoriana proléptica."""
    if month <= 2:
        correction = 0
    elif gregorian_is_leap(year):
        correction = -1
    else:
        correction = -2
    return (
        365 * (year - 1)
        + (year - 1) // 4
        - (year - 1) // 100
        + (year - 1) // 400
        + (367 * month - 362) // 12
        + correction
        + day
    )


def _gregorian_year_from_fixed(fixed: int) -> int:
    d0 = fixed - 1
    n400, d1 = divmod(d0, 146097)
    n100, d2 = divmod(d1, 36524)
    n4, d3 = divmod(d2, 1461)
    n1 = d3 // 365
    year = 400 * n400 + 100 * n100 + 4 * n4 + n1
    return year if (n100 == 4 or n1 == 4) else year + 1


def gregorian_from_fixed(fixed: int) -> tuple[int, int, int]:
    year = _gregorian_year_from_fixed(fixed)
    prior_days = fixed - fixed_from_gregorian(year, 1, 1)
    if fixed < fixed_from_gregorian(year, 3, 1):
        correction = 0
    elif gregorian_is_leap(year):
        correction = 1
    else:
        correction = 2
    month = (12 * (prior_days + correction) + 373) // 367
    day = fixed - fixed_from_gregorian(year, month, 1) + 1
    return year, month, day


def fixed_from_date(d: _date) -> int:
    return fixed_from_gregorian(d.year, d.month, d.day)


def date_from_fixed(fixed: int) -> _date:
    return _date(*gregorian_from_fixed(fixed))


# --------------------------------------------------------------------------- #
# Estrutura do ano hebraico
# --------------------------------------------------------------------------- #
def hebrew_leap_year(year: int) -> bool:
    """Um ano hebraico é bissexto 7 vezes em cada ciclo de 19 anos."""
    return (7 * year + 1) % 19 < 7


def last_month_of_hebrew_year(year: int) -> int:
    return 13 if hebrew_leap_year(year) else 12


def _elapsed_days(year: int) -> int:
    """Dias do epoch hebraico até o início (sem correção) de `year` (via molad)."""
    months_elapsed = (235 * year - 234) // 19
    parts_elapsed = 12084 + 13753 * months_elapsed
    day = 29 * months_elapsed + parts_elapsed // 25920
    # Dehiyyah: se o molad cai tarde, adia Rosh Hashanah em um dia (regra de dia da semana).
    if (3 * (day + 1)) % 7 < 3:
        day += 1
    return day


def _new_year_delay(year: int) -> int:
    """Dehiyyot restantes que ajustam a duração do ano (GaTaRaD / BeTUTaKPaT)."""
    ny0 = _elapsed_days(year - 1)
    ny1 = _elapsed_days(year)
    ny2 = _elapsed_days(year + 1)
    if ny2 - ny1 == 356:
        return 2
    if ny1 - ny0 == 382:
        return 1
    return 0


def hebrew_new_year(year: int) -> int:
    """RD de 1 Tishri de `year` (Rosh Hashanah)."""
    return HEBREW_EPOCH + _elapsed_days(year) + _new_year_delay(year)


def days_in_hebrew_year(year: int) -> int:
    return hebrew_new_year(year + 1) - hebrew_new_year(year)


def _long_marheshvan(year: int) -> bool:
    return days_in_hebrew_year(year) in (355, 385)


def _short_kislev(year: int) -> bool:
    return days_in_hebrew_year(year) in (353, 383)


def last_day_of_hebrew_month(year: int, month: int) -> int:
    if month in (2, 4, 6, 10, 13):
        return 29
    if month == 12 and not hebrew_leap_year(year):
        return 29
    if month == 8 and not _long_marheshvan(year):
        return 29
    if month == 9 and _short_kislev(year):
        return 29
    return 30


# --------------------------------------------------------------------------- #
# Hebraico <-> fixed
# --------------------------------------------------------------------------- #
def fixed_from_hebrew(year: int, month: int, day: int) -> int:
    """Número do dia RD para uma data hebraica."""
    if month < 7:  # Nisan..Elul vêm *depois* de Tishri no ano civil
        head = sum(
            last_day_of_hebrew_month(year, m)
            for m in range(7, last_month_of_hebrew_year(year) + 1)
        )
        head += sum(last_day_of_hebrew_month(year, m) for m in range(1, month))
    else:  # Tishri..(Adar/Adar II)
        head = sum(last_day_of_hebrew_month(year, m) for m in range(7, month))
    return hebrew_new_year(year) + head + day - 1


def hebrew_from_fixed(fixed: int) -> tuple[int, int, int]:
    # Limite inferior para o ano, depois avança. Dividir por 366 subestima o número
    # de anos hebraicos (média ~365.25 d), então `year` é um limite inferior seguro.
    year = (fixed - HEBREW_EPOCH) // 366 + 1
    while hebrew_new_year(year + 1) <= fixed:
        year += 1
    # Antes de Nisan 1 => ainda no trecho Tishri..Adar (meses 7..13), que vem primeiro
    # no ano civil; caso contrário Nisan..Elul (meses 1..6).
    start_month = 7 if fixed < fixed_from_hebrew(year, 1, 1) else 1
    month = start_month
    while fixed > fixed_from_hebrew(year, month, last_day_of_hebrew_month(year, month)):
        month += 1
    day = fixed - fixed_from_hebrew(year, month, 1) + 1
    return year, month, day


def hebrew_year_of(d: _date) -> int:
    return hebrew_from_fixed(fixed_from_date(d))[0]
