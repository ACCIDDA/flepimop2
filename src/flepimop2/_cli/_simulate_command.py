"""Simulate command implementation."""

__all__ = []


import click

from flepimop2._cli._cli_command import CliCommand


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
        click.echo(f"Simulating with config: {config}")
        click.echo(f"Verbosity level: {verbosity}")
        if dry_run:
            click.echo("Dry run mode: ENABLED")
