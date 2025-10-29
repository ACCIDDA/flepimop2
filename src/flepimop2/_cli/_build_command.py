"""Build command implementation."""

__all__ = []


from flepimop2._cli._cli_command import CliCommand


class BuildCommand(CliCommand):
    """Compile and build a model defined in a configuration file."""

    options = ("config", "verbosity", "dry_run")

    def run(self, *, config: str, verbosity: int, dry_run: bool) -> None:  # type: ignore[override]
        """
        Execute the build.

        Args:
            config: Path to the configuration file.
            verbosity: Verbosity level (0-3).
            dry_run: Whether dry run mode is enabled.
        """
        msg = "`BuildCommand.run` is not yet implemented."
        raise NotImplementedError(msg)
