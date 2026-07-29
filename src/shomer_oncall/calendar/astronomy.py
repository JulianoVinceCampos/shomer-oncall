"""Eventos solares (sunset e twilight por depression angle) dos primeiros princípios.

Implementa a "sunrise equation" padrão (modelo solar de baixa precisão, estilo NOAA)
em Python puro, retornando instants timezone-aware em UTC. Corrige refração
atmosférica + raio solar (o padrão de 0.833 graus) e a elevação do observador
(horizon dip ~= 0.0347*sqrt(h_metros) graus). Precisão de ~1-2 minutos, bem dentro
do candle-lighting buffer, então nunca pode causar uma violação de escala
(ver docs/METRICS.md#boundary-accuracy).

Sem dependências de terceiros: é isto que torna os boundaries determinísticos e
reproduzíveis offline (docs/adr/0002).
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

_UNIX_EPOCH_JD = 2440587.5
_OBLIQUITY_DEG = 23.4397


class NoSolarEventError(Exception):
    """Levantado em latitudes altas quando o sol nunca atinge o ângulo alvo
    (polar day/night). Os callers fazem fallback para uma regra de fixed minutes."""

    def __init__(self, kind: str) -> None:
        super().__init__(f"nenhum evento solar: {kind}")
        self.kind = kind


def _julian_day(year: int, month: int, day: int) -> float:
    """Julian Day às 12:00 UT da data gregoriana informada."""
    if month <= 2:
        year -= 1
        month += 12
    a = year // 100
    b = 2 - a + a // 4
    return math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + b - 1524.5


def _jd_to_datetime(jd: float) -> datetime:
    seconds = (jd - _UNIX_EPOCH_JD) * 86400.0
    return datetime(1970, 1, 1, tzinfo=UTC) + timedelta(seconds=seconds)


def _horizon_dip_deg(elevation_m: float) -> float:
    if elevation_m <= 0:
        return 0.0
    return 0.0347 * math.sqrt(elevation_m)


def solar_event(
    year: int,
    month: int,
    day: int,
    latitude: float,
    longitude: float,
    elevation_m: float,
    depression_deg: float,
    event: str,
) -> datetime:
    """Instant UTC de um evento solar na data informada.

    `depression_deg` é quão abaixo do horizonte está o centro do sol no evento
    (0.833 para o sunset geométrico incl. refração; ex. 8.5 para uma opinião de
    tzais). `event` é "sunset" ou "sunrise". O dip de elevação é somado
    automaticamente. Levanta NoSolarEventError quando o sol nunca atinge o ângulo.
    """
    if event not in ("sunset", "sunrise"):
        raise ValueError(f"event deve ser 'sunset' ou 'sunrise', recebido {event!r}")

    angle = depression_deg + _horizon_dip_deg(elevation_m)

    jd = _julian_day(year, month, day)
    # Contagem inteira de dias desde o epoch J2000.0. Arredondar é essencial: `jd`
    # está às 00:00 UT, e manter o meio-dia deslocaria o transit em ~12h.
    n = round(jd - 2451545.0 + 0.0008)
    j_star = n - longitude / 360.0  # tempo solar médio, longitude leste positiva

    # Anomalia média solar.
    m = math.radians((357.5291 + 0.98560028 * j_star) % 360)
    # Equation of the center.
    c = 1.9148 * math.sin(m) + 0.0200 * math.sin(2 * m) + 0.0003 * math.sin(3 * m)
    # Longitude eclíptica.
    lam = math.radians((math.degrees(m) + c + 180.0 + 102.9372) % 360)
    # Solar transit (Julian date do meio-dia solar nesta longitude).
    j_transit = 2451545.0 + j_star + 0.0053 * math.sin(m) - 0.0069 * math.sin(2 * lam)
    # Declinação.
    sin_dec = math.sin(lam) * math.sin(math.radians(_OBLIQUITY_DEG))
    dec = math.asin(sin_dec)

    lat = math.radians(latitude)
    cos_omega = (
        math.sin(math.radians(-angle)) - math.sin(lat) * math.sin(dec)
    ) / (math.cos(lat) * math.cos(dec))
    if cos_omega > 1:
        raise NoSolarEventError("sol sempre abaixo do ângulo (polar night)")
    if cos_omega < -1:
        raise NoSolarEventError("sol sempre acima do ângulo (polar day)")

    omega = math.degrees(math.acos(cos_omega))
    j_event = j_transit + (omega if event == "sunset" else -omega) / 360.0
    return _jd_to_datetime(j_event)


def sunset(
    year: int, month: int, day: int, latitude: float, longitude: float, elevation_m: float
) -> datetime:
    """Sunset geométrico (borda superior), corrigido por refração + elevação."""
    return solar_event(year, month, day, latitude, longitude, elevation_m, 0.833, "sunset")


def nightfall(
    year: int,
    month: int,
    day: int,
    latitude: float,
    longitude: float,
    elevation_m: float,
    depression_deg: float,
) -> datetime:
    """Tzais em um dado depression angle solar."""
    return solar_event(
        year, month, day, latitude, longitude, elevation_m, depression_deg, "sunset"
    )
