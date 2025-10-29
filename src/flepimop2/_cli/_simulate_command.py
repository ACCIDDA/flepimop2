"""Simulate command implementation."""

__all__ = []


from flepimop2._cli._cli_command import CliCommand


class SimulateCommand(CliCommand):
    """
    Run simulations based on a configuration file.

    This command runs epidemic simulations specified from a provided configuration file.
    The `CONFIG` argument should point to a valid configuration file.
    """

    options = ("config", "verbosity", "dry_run")

    def run(self, *, config: str, verbosity: int, dry_run: bool) -> None:  # type: ignore[override]
        """
        Execute the simulation.

        Args:
            config: Path to the configuration file.
            verbosity: Verbosity level (0-3).
            dry_run: Whether dry run mode is enabled.
        """
        msg = "`SimulateCommand.run` is not yet implemented."
        raise NotImplementedError(msg)
