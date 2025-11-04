"""Build command implementation."""

__all__ = []


from flepimop2._cli._cli_command import CliCommand


class BuildCommand(CliCommand):
    """Compile and build a model defined in a configuration file."""

    def run(self, *, config: str, dry_run: bool) -> None:  # type: ignore[override]
        """
        Execute the build.

        Args:
            config: Path to the configuration file.
            dry_run: Whether dry run mode is enabled.
        """
        msg = "`BuildCommand.run` is not yet implemented."
        raise NotImplementedError(msg)
