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
"""Shell job runner for flepimop2. For development and testing only."""

__all__ = ["ShellJob"]

import os
import shlex
import shutil
import subprocess  # noqa: S404
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Self

from pydantic import Field, PrivateAttr, model_validator

from flepimop2.exceptions import ValidationIssue
from flepimop2.job.abc import (
    SERIAL,
    JobABC,
    JobDryRun,
    JobHandle,
    JobStatus,
    JobStatusResult,
)
from flepimop2.job.shell._runner import _ShellPlanRunner
from flepimop2.process._plan import ProcessPlan
from flepimop2.process.abc import resolve_plan
from flepimop2.typing import override

if TYPE_CHECKING:
    from flepimop2.cli import CliCommand


class ShellJob(JobABC, module="shell"):
    """Run a command locally via subprocess. For dev/testing — not production.

    Attributes:
        module: The fully-qualified module name, resolved from `module="shell"` to
            `"flepimop2.job.shell"`.
        execution: Serial command execution or dependency-aware parallel plans.
        max_workers: Maximum concurrent workers when executing a plan.
        cwd: Optional working directory for the subprocess.
        env: Optional environment variables for the subprocess. If `None`,
            the current process environment is inherited.
        detach: If `True` (the default), the subprocess runs detached in a new
            session and control returns immediately. If `False`, the call blocks
            until the subprocess exits (useful for tests).
    """

    supports_plan: ClassVar[bool] = True
    execution: Literal["serial", "parallel"] = SERIAL
    max_workers: int = Field(default=4, ge=1)

    cwd: Path | None = None
    env: dict[str, str] | None = None
    detach: bool = True

    _exe: str | None = PrivateAttr(default=None)

    @model_validator(mode="after")
    def _validate_parallel_detach(self) -> Self:
        """Require blocking execution for parallel shell jobs.

        Returns:
            The validated ShellJob instance.

        Raises:
            ValueError: If parallel execution explicitly enables detachment.
        """
        if self.execution == "parallel":
            if "detach" not in self.model_fields_set:
                self.detach = False
            elif self.detach:
                msg = "Parallel ShellJob execution requires detach=False."
                raise ValueError(msg)
        return self

    @override
    def _submit_validate(self) -> list[ValidationIssue]:
        """Resolve the `flepimop2` executable and cache it for use in `_submit`.

        Returns:
            An empty list if the executable is found, or a one-element list
            containing a `ValidationIssue` if it cannot be located on PATH.
        """
        if self._exe is None:
            self._exe = shutil.which("flepimop2")
        if self._exe is None:
            return [
                ValidationIssue(
                    msg="Could not locate the 'flepimop2' executable on PATH.",
                    kind="missing_executable",
                )
            ]
        return []

    @override
    def _submit(
        self, command: "CliCommand", *, dry_run: bool = False
    ) -> JobHandle | JobDryRun:
        """Submit `command` as a local subprocess.

        Resolves the executable and assembles the argv regardless of `dry_run`;
        when `dry_run` is `True` it stops just before spawning the subprocess
        and returns a `JobDryRun` describing the command it would have run.

        Args:
            command: The CLI command instance to run.
            dry_run: If `True`, prepare the command but do not spawn it.

        Returns:
            A handle for the submitted subprocess, or a `JobDryRun` describing
            the skipped subprocess when `dry_run=True`.

        Raises:
            FileNotFoundError: If the `flepimop2` executable cannot be found on PATH.
        """
        if self._exe is None:
            self._exe = shutil.which("flepimop2")
        if self._exe is None:
            msg = "Could not locate the 'flepimop2' executable on PATH."
            raise FileNotFoundError(msg)
        argv = [self._exe, command.command_name(), *command.to_argv()]
        env: dict[str, str] | None = self.env
        kwargs: dict[str, Any] = {
            "cwd": self.cwd,
            "env": env,
        }
        if dry_run:
            details: dict[str, str] = {
                "mode": "detached" if self.detach else "blocking"
            }
            if self.cwd is not None:
                details["cwd"] = str(self.cwd)
            return JobDryRun(command=shlex.join(argv), details=details)
        if self.detach:
            proc = subprocess.Popen(argv, start_new_session=True, **kwargs)  # noqa: S603
            job_id = str(proc.pid)
            metadata: dict[str, Any] = {"mode": "detached"}
        else:
            result = subprocess.run(argv, check=False, **kwargs)  # noqa: S603
            job_id = str(result.returncode)
            metadata = {"mode": "blocking", "returncode": result.returncode}
        return JobHandle(job_id=job_id, backend="shell", metadata=metadata)

    @override
    def _submit_plan(
        self,
        plan: ProcessPlan,
        *,
        dry_run: bool = False,
    ) -> dict[str, JobHandle] | JobDryRun:
        """Execute independent process steps concurrently.

        Validate the dependency graph before execution. Run eligible
        steps concurrently, respecting dependencies and max_workers.

        Parallel execution is blocking so that dependencies and process
        failures can be monitored.

        Args:
            plan: Process steps with commands and dependencies.
            dry_run: If True, describe execution without launching processes.

        Returns:
            Completed job handles keyed by step, or a dry-run description.

        Raises:
            ValueError: If detached parallel execution is requested.
            NotImplementedError: If the platform does not support POSIX processes.
        """
        if self.detach:
            msg = "Parallel ShellJob execution requires detach=False."
            raise ValueError(msg)

        if os.name != "posix":
            msg = "Parallel ShellJob execution requires a POSIX system."
            raise NotImplementedError(msg)

        # Validate dependencies before launching any processes.
        ordered_steps = resolve_plan(plan)
        commands = self._prepare_plan_commands(plan, ordered_steps)

        if dry_run:
            return self._describe_plan(commands)

        return _ShellPlanRunner(
            plan,
            commands,
            max_workers=self.max_workers,
            cwd=self.cwd,
            env=self.env,
        ).run()

    def _describe_plan(self, commands: dict[str, list[str]]) -> JobDryRun:
        """Describe a prepared plan without launching workers.

        Returns:
            Commands and execution options for the skipped submission.
        """
        details = {"mode": "parallel", "max_workers": str(self.max_workers)}
        if self.cwd is not None:
            details["cwd"] = str(self.cwd)
        return JobDryRun(
            command="\n".join(
                f"{step}: {shlex.join(argv)}" for step, argv in commands.items()
            ),
            details=details,
        )

    def _prepare_plan_commands(
        self,
        plan: ProcessPlan,
        ordered_steps: list[str],
    ) -> dict[str, list[str]]:
        """Resolve and validate commands before execution.

        Args:
            plan: Process steps containing commands and dependencies.
            ordered_steps: Process step names in dependency order.

        Returns:
            Commands keyed by process step name.

        Raises:
            FileNotFoundError: If the flepimop2 executable is not found.
            ValueError: If a planned command is invalid.
        """
        if self._exe is None:
            self._exe = shutil.which("flepimop2")

        if self._exe is None:
            msg = "Could not locate the 'flepimop2' executable on PATH."
            raise FileNotFoundError(msg)

        commands: dict[str, list[str]] = {}

        for step in ordered_steps:
            argv = plan[step]["command"]

            if len(argv) < 2 or argv[0] != "flepimop2":
                msg = f"Invalid flepimop2 command for step '{step}'."
                raise ValueError(msg)

            commands[step] = [self._exe, *argv[1:]]

        return commands

    def _status(self, handle: JobHandle) -> JobStatusResult:  # noqa: PLR6301
        """Report the status of a previously submitted shell job.

        For blocking submissions the handle's `job_id` is the subprocess return
        code, so the status is derived directly from it. For detached
        submissions the `job_id` is a PID, which is probed for liveness with
        `os.kill(pid, 0)`:

        - A live PID reports `RUNNING`.
        - A `ProcessLookupError` means the process has already exited; because a
          detached process cannot be reaped here, its exit code is unknown and
          the status is reported as `FINISHED_UNKNOWN`.
        - A `PermissionError` means the PID exists but is owned by another user,
          so it is still considered `RUNNING`.

        Args:
            handle: The handle returned when the job was submitted.

        Returns:
            A `JobStatusResult` describing the job's current state.
        """
        detail = {}
        if handle.metadata.get("mode") == "blocking":
            returncode = int(handle.metadata.get("returncode", handle.job_id))
            status = JobStatus.SUCCESSFUL if returncode == 0 else JobStatus.FAILED
            detail = {"returncode": returncode}
        else:
            pid = int(handle.job_id)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                status = JobStatus.FINISHED_UNKNOWN
            except PermissionError:
                status = JobStatus.RUNNING
            else:
                status = JobStatus.RUNNING
        return JobStatusResult(
            job_id=handle.job_id,
            backend=handle.backend,
            submitted_at=handle.submitted_at,
            metadata=handle.metadata,
            status=status,
            detail=detail,
        )
