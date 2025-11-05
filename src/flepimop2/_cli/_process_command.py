"""Simulate command implementation."""

__all__ = []

from pathlib import Path

import flepimop2.process as process_module
from flepimop2._cli._cli_command import CliCommand
from flepimop2._utils._click import _get_config_target
from flepimop2.configuration import ConfigurationModel


class ProcessCommand(CliCommand):
    """
    Execute a processing step based on a configuration file.

    The `CONFIG` argument should point to a valid configuration file.
    """

    def run(  # type: ignore[override]
        self,
        *,
        config: Path,
        dry_run: bool,
        target: str | None = None,
    ) -> None:
        """
        Execute the processing step.

        Args:
            config: Path to the configuration file.
            dry_run: Whether dry run mode is enabled.
            target: Optional target process config to use.
        """
        configmodel = ConfigurationModel.from_yaml(config)
        processconfig = configmodel.process
        processtarget = _get_config_target(processconfig, target)

        self.info(f"Processing configuration file: {config}")
        self.info(f"Process section: {processconfig}")
        self.info(f"Process target: {processtarget}")

        process_instance = process_module.build(processtarget)
        process_instance.execute(dry_run=dry_run)
