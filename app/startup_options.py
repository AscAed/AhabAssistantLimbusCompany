"""Command-line options that affect application startup."""

from __future__ import annotations

SKIP_STARTUP_NETWORK_CHECKS_ARG = "--skip-startup-network-checks"


def has_skip_startup_network_checks(argv: list[str]) -> bool:
    """Return whether argv requests skipping automatic remote startup checks."""
    return SKIP_STARTUP_NETWORK_CHECKS_ARG in argv[1:]


def filter_startup_network_checks_arg(argv: list[str]) -> list[str]:
    """Remove the application-only option before passing args to Qt or task parsing."""
    return [argument for argument in argv if argument != SKIP_STARTUP_NETWORK_CHECKS_ARG]
