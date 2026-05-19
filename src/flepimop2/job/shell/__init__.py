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

import shutil
import subprocess  # noqa: S404
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import PrivateAttr

from flepimop2.exceptions import ValidationIssue
from flepimop2.job.abc import JobABC, JobHandle

if TYPE_CHECKING:
    from flepimop2._cli._cli_command import CliCommand


class ShellJob(JobABC, module="shell"):
    """Run a command locally via subprocess. For dev/testing — not production.

    Attributes:
        module: The fully-qualified module name, resolved from `module="shell"` to
            `"flepimop2.job.shell"`.
        cwd: Optional working directory for the subprocess.
        env: Optional environment variables for the subprocess. If `None`,
            the current process environment is inherited.
        detach: If `True` (the default), the subprocess runs detached in a new
            session and control returns immediately. If `False`, the call blocks
            until the subprocess exits (useful for tests).
    """

    cwd: Path | None = None
    env: dict[str, str] | None = None
    detach: bool = True

    _exe: str | None = PrivateAttr(default=None)

    def _submit_validate(self) -> list[ValidationIssue] | None:
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

    def _submit(self, command: "CliCommand") -> JobHandle:
        """Submit `command` as a local subprocess.

        Args:
            command: The CLI command instance to run.

        Returns:
            A handle for the submitted subprocess.

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
        if self.detach:
            proc = subprocess.Popen(argv, start_new_session=True, **kwargs)  # noqa: S603
            job_id = str(proc.pid)
        else:
            result = subprocess.run(argv, check=False, **kwargs)  # noqa: S603
            job_id = str(result.returncode)
        return JobHandle(job_id=job_id, backend="shell")
