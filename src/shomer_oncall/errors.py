"""Erros de domínio tipados; cada um mapeia para um exit code da CLI (ver docs/CLI.md)."""

from __future__ import annotations


class ShomerError(Exception):
    """Classe base de todos os erros de domínio. `exit_code` orienta a CLI."""

    exit_code = 1


class ConfigError(ShomerError):
    exit_code = 1


class InvalidTeamError(ShomerError):
    exit_code = 5


class UnknownShitahError(ShomerError):
    exit_code = 5


class InfeasibleScheduleError(ShomerError):
    exit_code = 5


class UncoveredShiftError(ShomerError):
    """Levantado em modo estrito quando um shift não tem nenhum membro feasible."""

    exit_code = 3


class HardViolationError(ShomerError):
    """Nunca deveria ocorrer; indica que a alocação violou um restricted interval."""

    exit_code = 2


class FairnessGateError(ShomerError):
    exit_code = 4
