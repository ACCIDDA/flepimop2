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
"""Abstract base class for flepimop2 job runners."""

__all__ = [
    "PARALLEL",
    "SERIAL",
    "JobABC",
    "JobDryRun",
    "JobExecutionMode",
    "JobHandle",
    "JobStatus",
    "JobStatusResult",
    "ProcessPlan",
    "build",
]

from abc import abstractmethod
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from pydantic import BaseModel, Field

from flepimop2._utils._module import _build
from flepimop2.exceptions import Flepimop2ValidationError, ValidationIssue
from flepimop2.module import ModuleBase
from flepimop2.process.abc import ProcessPlan
from flepimop2.typing import override

if TYPE_CHECKING:
    from flepimop2.cli import CliCommand

JobExecutionMode = Literal["serial", "parallel"]
SERIAL: JobExecutionMode = "serial"
PARALLEL: JobExecutionMode = "parallel"


class JobHandle(BaseModel):
    """A reference to a submitted job.

    Modeled with `pydantic` so handles can be serialized to and parsed from
    JSON (with validation) for persistent caching.

    Attributes:
        job_id: Opaque token identifying the job on the backend
            (PID, Slurm id, ARN, ...).
        backend: The job module name that produced this handle.
        submitted_at: When the job was submitted.
        metadata: Optional backend-specific metadata (partition, queue, ...).
    """

    job_id: str
    backend: str
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __str__(self) -> str:
        """Return a short, single-line representation suitable for stdout."""
        ts = self.submitted_at.strftime("%Y-%m-%dT%H:%M:%S")
        return f"{self.backend}-{self.job_id} submitted_at={ts}"


class JobStatus(StrEnum):
    """The lifecycle state of a submitted job.

    Attributes:
        PENDING: The job has been accepted but has not started running.
        RUNNING: The job is currently executing.
        SUCCESSFUL: The job finished and is believed to have succeeded.
        FAILED: The job finished and is believed to have failed.
        FINISHED_UNKNOWN: The job finished but its success or failure could not
            be determined (e.g. a detached subprocess whose exit code can no
            longer be recovered).
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    FINISHED_UNKNOWN = "finished_unknown"

    @property
    def is_finished(self) -> bool:
        """Whether this status represents a terminal (finished) state."""
        return self in {
            JobStatus.SUCCESSFUL,
            JobStatus.FAILED,
            JobStatus.FINISHED_UNKNOWN,
        }


class JobStatusResult(JobHandle):
    """The status of a submitted job.

    A `JobHandle` enriched with the job's current lifecycle `status` and an
    optional, backend-specific `detail` payload.

    Attributes:
        status: The current lifecycle state of the job.
        detail: Optional backend-specific status details (exit code, queue
            position, node assignment, ...).
    """

    status: JobStatus
    detail: dict[str, Any] = Field(default_factory=dict)

    def __str__(self) -> str:
        """Return a short, single-line representation suitable for stdout."""
        return f"{super().__str__()} status={self.status.value}"


class JobDryRun(BaseModel):
    """A description of the submission a dry run skipped.

    Returned by `JobABC.submit` (in place of a `JobHandle`) when `dry_run` is
    requested, so the caller can report exactly what *would* have been submitted
    without actually submitting it.

    Attributes:
        command: The command the backend would have run, rendered for display
            (e.g. `flepimop2 simulate ...` for the shell backend, or
            `sbatch ...` for a Slurm backend).
        details: Optional backend-specific specifics about the skipped submission
            (working directory, partition, generated script path, ...).
    """

    command: str
    details: dict[str, str] = Field(default_factory=dict)


class JobABC(ModuleBase, module_namespace="job"):
    """Abstract base class for flepimop2 job runners.

    Backends support ordinary command submission through :meth:`submit`.
    Backends that support dependency-aware process plans should set
    ``supports_plan`` to ``True`` and either implement :meth:`_submit_step`
    or override :meth:`_submit_plan`.

    Backends that support asynchronous/detached submission of dependency-aware
    plans (e.g. cluster schedulers that support native job dependencies) should
    also set ``supports_detached_plan`` to ``True``. When detached execution
    is requested on a backend without detached plan support, the CLI
    automatically falls back to monolithic submission.

    The ``execution`` field controls the execution strategy: ``serial``
    (default) or ``parallel``.
    """

    # Plan submission is optional so existing submit-only backends remain valid.
    # Default execution is serial.
    supports_plan: ClassVar[bool] = False
    supports_detached_plan: ClassVar[bool] = False
    execution: JobExecutionMode = SERIAL

    def submit(
        self, command: "CliCommand", *, dry_run: bool = False
    ) -> JobHandle | JobDryRun:
        """Submit `command` for execution on this job backend.

        Runs `_submit_validate` first; if issues are found they are raised as
        a `Flepimop2ValidationError`. The `dry_run` flag is forwarded to
        `_submit` so that backends can perform all of the work leading up to a
        submission (rendering batch scripts, staging files, resolving
        resources, ...) and then stop just before the submission itself,
        returning a `JobDryRun` that describes what would have been submitted.

        Args:
            command: The CLI command instance to submit.
            dry_run: If `True`, perform preflight work but do not actually
                submit.

        Returns:
            A `JobHandle` for the submitted work unit, or a `JobDryRun`
            describing the skipped submission when `dry_run=True`.

        Raises:
            Flepimop2ValidationError: If `_submit_validate` returns issues.
        """
        if issues := self.validate_module():
            raise Flepimop2ValidationError(issues)
        return self._submit(command, dry_run=dry_run)

    @abstractmethod
    def _submit(
        self, command: "CliCommand", *, dry_run: bool = False
    ) -> JobHandle | JobDryRun:
        """Backend-specific submission implementation.

        Implementations should perform all preparatory work (rendering batch
        scripts, staging inputs, resolving resources, ...) regardless of
        `dry_run`, and only skip the final, irreversible submission step when
        `dry_run` is `True`, returning a `JobDryRun` that describes what would
        have been submitted in that case.

        Args:
            command: The CLI command instance to submit.
            dry_run: If `True`, do everything except the actual submission and
                return a `JobDryRun`.

        Returns:
            A `JobHandle` for the submitted work unit, or a `JobDryRun`
            describing the skipped submission when `dry_run=True`.
        """
        ...

    @override
    def validate_module(self) -> list[ValidationIssue]:
        """Validate that this backend is ready to accept submissions.

        Returns:
            A list of `ValidationIssue` objects (empty if valid).
        """
        return self._submit_validate()

    def _submit_validate(self) -> list[ValidationIssue]:  # noqa: PLR6301
        """Validate that this backend is ready to accept submissions.

        Called by `submit` before delegating to `_submit`. Subclasses may
        override to perform backend-specific preflight checks (e.g. resolving
        executables, checking credentials, testing connectivity).

        Returns:
            A list of `ValidationIssue` objects if validation fails, or an empty
            list if valid.
        """
        return []

    def submit_plan(
        self,
        plan: ProcessPlan,
        *,
        dry_run: bool = False,
    ) -> dict[str, JobHandle] | JobDryRun:
        """Submit a dependency-aware process plan.

        This entry point is available on every backend for a stable interface,
        but only backends advertising ``supports_plan = True`` should be
        dispatched here. Submit-only backends retain the existing
        :meth:`submit` path.

        Args:
            plan: Process steps and their dependency names.
            dry_run: If ``True``, prepare the submission without submitting it.

        Returns:
            Handles keyed by process-step name, or a description of the
            submission that was skipped for a dry run.

        Raises:
            Flepimop2ValidationError: If backend validation fails.
        """
        if issues := self.validate_module():
            raise Flepimop2ValidationError(issues)

        return self._submit_plan(plan, dry_run=dry_run)

    def _submit_step(
        self,
        step_name: str,
        command: list[str],
        depends_on: list[JobHandle],
        *,
        dry_run: bool = False,
    ) -> JobHandle | JobDryRun:
        """Backend-specific single step submission implementation.

        Called by the default :meth:`_submit_plan` implementation for each
        step in dependency order. Subclasses can override this method to
        support step-level scheduling without needing to implement full DAG
        traversal.

        Args:
            step_name: The name of the process step.
            command: The command-line argv for executing this step.
            depends_on: Handles of prerequisite steps this step depends on.
            dry_run: If ``True``, prepare the step without submitting it.

        Raises:
            NotImplementedError: If not implemented by the backend subclass.
        """
        msg = (
            f"Job backend '{self.module}' does not support dependency-aware plans: "
            "neither _submit_plan nor _submit_step is implemented."
        )
        raise NotImplementedError(msg)

    def _submit_plan(
        self,
        plan: ProcessPlan,
        *,
        dry_run: bool = False,
    ) -> dict[str, JobHandle] | JobDryRun:
        """Implement dependency-aware plan submission.

        The default implementation iterates through `plan` in order, resolves
        the `JobHandle` of each prerequisite step, and delegates to
        :meth:`_submit_step`.

        Subclasses with native DAG or bulk submission APIs (e.g. workflow engines
        or orchestrators) can override this method directly.

        Args:
            plan: Process steps and their dependency names.
            dry_run: If ``True``, prepare the submission without submitting it.

        Returns:
            Handles keyed by process-step name, or a `JobDryRun` describing the
            skipped submission.
        """
        handles: dict[str, JobHandle] = {}
        dry_runs: dict[str, JobDryRun] = {}

        for step_name, step_spec in plan.items():
            depends_names = step_spec.get("depends", [])
            dep_handles = [handles[dep] for dep in depends_names if dep in handles]

            step_res = self._submit_step(
                step_name,
                step_spec["command"],
                dep_handles,
                dry_run=dry_run,
            )
            if isinstance(step_res, JobDryRun):
                dry_runs[step_name] = step_res
            else:
                handles[step_name] = step_res

        if dry_run:
            details = {
                f"step_{idx}": f"{name} (depends: {step_spec.get('depends', [])})"
                for idx, (name, step_spec) in enumerate(plan.items())
            }
            commands = [
                f"# Step: {name}\n{dr.command}" for name, dr in dry_runs.items()
            ]
            return JobDryRun(
                command="\n\n".join(commands),
                details=details,
            )

        return handles

    def status(self, handle: JobHandle) -> JobStatusResult:
        """Query the status of a previously submitted job.

        Runs `_status_validate` first; if issues are found they are raised as
        a `Flepimop2ValidationError`. Otherwise delegates to `_status`.

        Args:
            handle: The handle returned when the job was submitted.

        Returns:
            A `JobStatusResult` describing the job's current state.

        Raises:
            Flepimop2ValidationError: If `_status_validate` returns issues.
        """
        if (issues := self._status_validate()) is not None and issues:
            raise Flepimop2ValidationError(issues)
        return self._status(handle)

    @abstractmethod
    def _status(self, handle: JobHandle) -> JobStatusResult:
        """Backend-specific status implementation.

        Args:
            handle: The handle returned when the job was submitted.

        Returns:
            A `JobStatusResult` describing the job's current state.
        """
        ...

    def _status_validate(self) -> list[ValidationIssue] | None:  # noqa: PLR6301
        """Validate that this backend is ready to report job status.

        Called by `status` before delegating to `_status`. Subclasses may
        override to perform backend-specific preflight checks (e.g. resolving
        executables, checking credentials, testing connectivity).

        Returns:
            A list of `ValidationIssue` objects if validation fails, an empty
            list if validation passes with no issues, or `None` if not
            implemented.
        """
        return None


def build(config: dict[str, Any] | ModuleBase | str) -> JobABC:
    """Build a `JobABC` from a configuration dictionary.

    Args:
        config: Configuration dictionary. The dict should contain a
            'module' key, which will be used to lookup the job module path.
            The module will have "flepimop2.job." prepended.

    Returns:
        The constructed job object.
    """
    return _build(config, "job", JobABC)  # type: ignore[type-abstract]
