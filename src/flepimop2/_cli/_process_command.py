"""Simulate command implementation."""

__all__ = []


from flepimop2._cli._cli_command import CliCommand
from flepimop2.configuration import ConfigurationModel


class ProcessCommand(CliCommand):
    """
    Execute a processing step based on a configuration file.

    The `CONFIG` argument should point to a valid configuration file.
    """

    options = ("config", "verbosity", "dry_run")

    def run(self, *, config: str, verbosity: int, dry_run: bool) -> None:  # type: ignore[override]
        """
        Execute the processing step.

        Args:
            config: Path to the configuration file.
            verbosity: Verbosity level (0-3).
            dry_run: Whether dry run mode is enabled.
        """
        configmodel = ConfigurationModel.from_yaml(config)
        processconfig = configmodel.process

        if (dry_run):
            self.info(msg=f"Processing configuration file: {config}")
            self.info(f"Process section: {processconfig}")
        