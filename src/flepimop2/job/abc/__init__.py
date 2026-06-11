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
    "JobABC",
    "JobDryRun",
    "JobHandle",
    "JobStatus",
    "JobStatusResult",
    "build",
]

from abc import abstractmethod
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from flepimop2._utils._module import _build
from flepimop2.exceptions import Flepimop2ValidationError, ValidationIssue
from flepimop2.module import ModuleBase

if TYPE_CHECKING:
    from flepimop2.cli import CliCommand


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
    """Abstract base class for flepimop2 job runners."""

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
        if (issues := self._submit_validate()) is not None and issues:
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

    def _submit_validate(self) -> list[ValidationIssue] | None:  # noqa: PLR6301
        """Validate that this backend is ready to accept submissions.

        Called by `submit` before delegating to `_submit`. Subclasses may
        override to perform backend-specific preflight checks (e.g. resolving
        executables, checking credentials, testing connectivity).

        Returns:
            A list of `ValidationIssue` objects if validation fails, an empty
            list if validation passes with no issues, or `None` if not
            implemented.
        """
        return None

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
