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
from flepimop2.process._plan import ProcessPlan
from flepimop2.process.abc import _declared_depends, resolve_plan
from flepimop2.process.abc import build as build_process
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

    def build_plan(self) -> ProcessPlan:
        """Build a dependency-aware execution plan without executing steps.

        Returns:
            A process plan containing commands and dependency names.

        Raises:
            ValueError: If no process configuration path is available.
        """
        config_path = self.config

        if config_path is None:
            msg = "Process configuration path is required"
            raise ValueError(msg)

        configmodel = ConfigurationModel.from_yaml(config_path)
        processconfig = configmodel.process

        requested_target, _ = _resolve_config_target(
            processconfig,
            self.bound_kwargs.get("target"),
            "process",
        )

        # Validate dependencies and obtain a topological ordering.
        ordered_steps = resolve_plan(processconfig, requested_target)

        plan: ProcessPlan = {}

        for step in ordered_steps:
            entry = processconfig[step]
            step_kwargs = {
                name: self.bound_kwargs[name]
                for name in type(self).options()
                if name in self.bound_kwargs and name != "dry_run"
            }
            step_kwargs["target"] = step
            step_kwargs["no_deps"] = True
            step_command = type(self)(**step_kwargs)

            plan[step] = {
                "command": [
                    "flepimop2",
                    step_command.command_name(),
                    *step_command.to_argv(),
                ],
                "depends": _declared_depends(entry),
            }

        return plan

    def run(  # type: ignore[override]
        self,
        *,
        config: Path,
        dry_run: bool,
        target: str | None = None,
        force: int = 0,
        no_deps: bool = False,
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
            no_deps: Whether to execute only the selected target without its
                dependencies.

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

        # Validate the dependency graph.
        ordered_steps = resolve_plan(processconfig, processtargetname)

        # A plan-capable backend handles dependencies between submitted steps.
        # Each individual invocation executes only its assigned step.
        plan = [processtargetname] if no_deps else ordered_steps

        if len(plan) > 1:
            self.info(f"Process plan: {' -> '.join(plan)}")
        else:
            self.info(f"Step {processtargetname}")

        for step in plan:
            process_instance = build_process(processconfig[step])
            # One -f forces just the step asked for, leaving its dependencies
            # to their own satisfied-means-skip behaviour; -ff forces those too.
            process_instance.execute(
                dry_run=dry_run,
                force=_should_force(force, step, processtargetname),
            )
        return ExitCode.OKAY
