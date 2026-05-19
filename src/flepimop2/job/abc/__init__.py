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

__all__ = ["JobABC", "JobHandle", "build"]

from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from flepimop2._utils._module import _build
from flepimop2.exceptions import Flepimop2ValidationError, ValidationIssue
from flepimop2.module import ModuleBase

if TYPE_CHECKING:
    from flepimop2._cli._cli_command import CliCommand


@dataclass
class JobHandle:
    """A reference to a submitted job.

    Attributes:
        job_id: Opaque token identifying the job on the backend (PID, Slurm id,
            ARN, ...).
        backend: The job module name that produced this handle.
        submitted_at: When the job was submitted.
        metadata: Optional backend-specific metadata (partition, queue, ...).
    """

    job_id: str
    backend: str
    submitted_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Return a short, single-line representation suitable for stdout."""
        ts = self.submitted_at.strftime("%Y-%m-%dT%H:%M:%S")
        return f"{self.backend}/{self.job_id} submitted_at={ts}"


class JobABC(ModuleBase, module_namespace="job"):
    """Abstract base class for flepimop2 job runners."""

    def submit(
        self, command: "CliCommand", *, dry_run: bool = False
    ) -> JobHandle | None:
        """Submit `command` for execution on this job backend.

        Runs `_submit_validate` first; if issues are found they are raised as
        a `Flepimop2ValidationError`. When `dry_run=True` the method returns
        `None` after validation without actually submitting.

        Args:
            command: The CLI command instance to submit.
            dry_run: If `True`, validate only — do not actually submit.

        Returns:
            A handle for the submitted work unit, or `None` when `dry_run=True`.

        Raises:
            Flepimop2ValidationError: If `_submit_validate` returns issues.
        """
        if (issues := self._submit_validate()) is not None and issues:
            raise Flepimop2ValidationError(issues)
        if dry_run:
            return None
        return self._submit(command)

    @abstractmethod
    def _submit(self, command: "CliCommand") -> JobHandle:
        """Backend-specific submission implementation.

        Args:
            command: The CLI command instance to submit.

        Returns:
            A handle for the submitted work unit.
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
