# flepimop2: The FLExible Pipeline for Interchangeable MOdel Processing
# Copyright (C) 2026  Carl Pearson, Joshua Macdonald, Timothy Willard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Simulate command implementation."""

__all__ = []

from pathlib import Path

from flepimop2._utils._click import _resolve_config_target
from flepimop2.cli._cli_command import CliCommand
from flepimop2.configuration import ConfigurationModel
from flepimop2.process.abc import build as build_process
from flepimop2.process.abc import expand_scenarios, resolve_plan, validate_scenarios
from flepimop2.typing import ExitCode

# `--force` is a counter so that forcing a step and forcing everything it needs
# are separate asks: one `-f` re-runs the step you named, a second also re-runs
# its dependencies.
_FORCE_TARGET = 1
_FORCE_DEPENDENCIES = 2


def _should_force(force: int, step: str, target: str | None) -> bool:
    """
    Decide whether one step of a plan runs regardless of being satisfied.

    Args:
        force: How many times `--force` was given.
        step: The plan step being considered.
        target: The step the user actually asked for.

    Returns:
        True if this step should run even when its target already exists.

    Examples:
        >>> from flepimop2.cli._process_command import _should_force
        >>> _should_force(0, "transform", "transform")
        False
        >>> _should_force(1, "transform", "transform")
        True
        >>> _should_force(1, "fetch", "transform")
        False
        >>> _should_force(2, "fetch", "transform")
        True

    """
    if force >= _FORCE_DEPENDENCIES:
        return True
    return force >= _FORCE_TARGET and step == target


class ProcessCommand(CliCommand):
    """
    Execute a processing step based on a configuration file.

    The `CONFIG` argument should point to a valid configuration file.
    """

    @property
    def target(self) -> str | None:
        """
        Get the resolved process target name.

        The returned value accounts for the implicit default target used when
        no `--target` option was provided.
        """
        configmodel = ConfigurationModel.from_yaml(self.bound_kwargs["config"])
        target, _ = _resolve_config_target(
            configmodel.process,
            self.bound_kwargs.get("target"),
            "process",
        )
        return target

    def run(  # type: ignore[override]
        self,
        *,
        config: Path,
        dry_run: bool,
        target: str | None = None,
        force: int = 0,
    ) -> ExitCode:
        """
        Execute the processing step and anything it depends on.

        The requested step's `depends` are resolved first, so asking for one
        step also runs whatever it needs, in dependency order. A step that
        reports its target already satisfied is skipped, which is what makes
        re-running a pipeline cheap.

        Args:
            config: Path to the configuration file.
            dry_run: Whether dry run mode is enabled.
            target: Optional target process config to use.
            force: How much of the plan to run regardless of whether its
                targets are already present. `0` skips satisfied steps, `1`
                (`-f`) forces only the requested step, so forcing a transform
                does not re-fetch its inputs, and `2` or more (`-ff`) forces
                its dependencies too.

        Returns:
            An exit code indicating success or failure.
        """
        configmodel = ConfigurationModel.from_yaml(config)
        processconfig = configmodel.process
        processtargetname, processtarget = _resolve_config_target(
            processconfig,
            target,
            "process",
        )

        self.info(f"Processing configuration file: {config}")
        self.info(f"Process section: {processconfig}")
        self.info(f"Process target: {processtargetname} => {processtarget}")

        plan = resolve_plan(processconfig, processtargetname)
        # Scenario references are checked across the whole section before any
        # step runs, for the same reason `depends` is: a typo should cost
        # nothing rather than surface partway through a pipeline.
        validate_scenarios(processconfig, configmodel.scenarios)
        if len(plan) > 1:
            self.info(f"Process plan: {' -> '.join(plan)}")

        for step in plan:
            # One -f forces just the step asked for, leaving its dependencies
            # to their own satisfied-means-skip behaviour; -ff forces those too.
            forced = _should_force(force, step, processtargetname)
            configs = expand_scenarios(processconfig[step], configmodel.scenarios)
            if len(configs) > 1:
                self.info(f"Step '{step}' runs {len(configs)} scenarios.")
            for config_ in configs:
                build_process(config_).execute(dry_run=dry_run, force=forced)
        return ExitCode.OKAY
