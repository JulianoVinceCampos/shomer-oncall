"""Modelo solar: faixas de plausibilidade (guarda de regressão) + monotonicidade."""

import pytest

from shomer_oncall.calendar import astronomy as A


def _seconds_utc(dt):
    return dt.hour * 3600 + dt.minute * 60 + dt.second


@pytest.mark.golden
def test_jerusalem_summer_sunset_in_window():
    # Sunset publicado de Jerusalém ~2024-06-21 é ~16:48 UTC (19:48 IDT). Janela larga
    # protege contra regressões grosseiras (ex. o bug de meio-dia no transit).
    ss = A.sunset(2024, 6, 21, 31.78, 35.22, 754)
    assert 16 * 3600 + 40 * 60 <= _seconds_utc(ss) <= 17 * 3600


@pytest.mark.golden
def test_sao_paulo_winter_sunset_in_window():
    ss = A.sunset(2026, 6, 12, -23.55, -46.63, 760)
    assert 20 * 3600 + 20 * 60 <= _seconds_utc(ss) <= 20 * 3600 + 45 * 60


def test_tzais_after_sunset():
    ss = A.sunset(2026, 6, 12, -23.55, -46.63, 760)
    tz = A.nightfall(2026, 6, 12, -23.55, -46.63, 760, 8.5)
    assert tz > ss


@pytest.mark.property
def test_stricter_opinion_never_earlier():
    # Depression angle maior => nightfall mais tarde (monotonicidade), qualquer data/local.
    for month in range(1, 13):
        t85 = A.nightfall(2026, month, 15, -23.55, -46.63, 760, 8.5)
        t161 = A.nightfall(2026, month, 15, -23.55, -46.63, 760, 16.1)
        assert t161 >= t85


def test_polar_night_raises():
    # Inverno profundo bem ao norte: o sol não atinge um tzais de 8.5 graus.
    with pytest.raises(A.NoSolarEventError):
        A.nightfall(2026, 12, 21, 78.0, 15.0, 0, 8.5)
