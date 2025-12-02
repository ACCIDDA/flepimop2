"""Simulate command implementation."""

__all__ = []

from pathlib import Path

from flepimop2._cli._cli_command import CliCommand
from flepimop2._utils._click import _get_config_target
from flepimop2.configuration import ConfigurationModel
from flepimop2.configuration._action import ActionModel
from flepimop2.process.abc import build as build_process


class ProcessCommand(CliCommand):
    """
    Execute a processing step based on a configuration file.

    The `CONFIG` argument should point to a valid configuration file.
    """

    def run(  # type: ignore[override]
        self,
        *,
        config: Path,
        target: str | None = None,
        out_config: Path | None = None,
        dry_run: bool = False,
    ) -> None:
        """
        Execute the processing step.

        Args:
            config: Path to the configuration file.
            target: Optional target process config to use.
            out_config: Optional path to write the resolved configuration to.
            dry_run: Whether dry run mode is enabled.
        """
        config_model = ConfigurationModel.from_yaml(config)
        process_config = config_model.process
        process_target = _get_config_target(process_config, target, "process")

        self.info(f"Processing configuration file: {config}")
        self.info(f"Process section: {process_config}")
        self.info(f"Process target: {process_target}")

        action = ActionModel(action="process", name=config_model.name)

        process_instance = build_process(process_target)
        process_instance.execute(configuration=config_model, dry_run=dry_run)

        if out_config is not None:
            config_model.history.append(action)
            config_model.to_yaml(out_config)
            self.debug(f"Wrote resolved configuration to: {out_config}")
