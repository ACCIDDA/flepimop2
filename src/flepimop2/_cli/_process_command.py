"""Simulate command implementation."""

__all__ = []

from pathlib import Path

import flepimop2.process as process_module
from flepimop2._cli._cli_command import CliCommand
from flepimop2.configuration import ConfigurationModel


class ProcessCommand(CliCommand):
    """
    Execute a processing step based on a configuration file.

    The `CONFIG` argument should point to a valid configuration file.
    """

    options = ("config", "verbosity", "dry_run")

    def run(self, *, config: Path, verbosity: int, dry_run: bool) -> None:  # type: ignore[override]
        """
        Execute the processing step.

        Args:
            config: Path to the configuration file.
            verbosity: Verbosity level (0-3).
            dry_run: Whether dry run mode is enabled.
        """
        configmodel = ConfigurationModel.from_yaml(config)
        processconfig = configmodel.process
        processtarget = next(iter(processconfig.keys()))

        self.info(f"Processing configuration file: {config}")
        self.info(f"Process section: {processconfig}")
        self.info(f"Process target: {processtarget}")

        process_instance = process_module.build(processconfig[processtarget])
        process_instance.execute(dry_run=dry_run)
