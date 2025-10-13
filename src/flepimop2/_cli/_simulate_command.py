"""Simulate command implementation."""

__all__ = []

from typing import Final

from flepimop2._cli._cli_command import CliCommand
from flepimop2.logging import get_script_logger


class SimulateCommand(CliCommand):
    """
    Run simulations based on a configuration file.

    This command runs epidemic simulations specified from a provided configuration file.
    The `CONFIG` argument should point to a valid configuration file.
    """

    options = ("config", "verbosity", "dry_run")

    @staticmethod
    def run(  # type: ignore[override]
        *, config: str, verbosity: int, dry_run: bool
    ) -> None:
        """
        Execute the simulation.

        Args:
            config: Path to the configuration file.
            verbosity: Verbosity level (0-3).
            dry_run: Whether dry run mode is enabled.
        """
        logger: Final = get_script_logger(__name__, verbosity)
        logger.info("Simulating with configuration file: %s", config)
        logger.info("Verbosity level set to: %d", verbosity)
        logger.debug("Dry run mode is %s", "ENABLED" if dry_run else "DISABLED")
