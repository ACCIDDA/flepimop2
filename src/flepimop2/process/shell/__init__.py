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
"""Shell process for flepimop2."""

__all__ = ["ShellProcess"]

import shlex
from pathlib import Path
from shutil import which
from subprocess import run  # noqa: S404

from click import echo
from pydantic import Field

from flepimop2.exceptions import Flepimop2ValidationError, ValidationIssue
from flepimop2.process.abc import ProcessABC
from flepimop2.typing import override


class ShellProcess(ProcessABC, module="shell"):
    """
    Shell process for executing commands.

    Attributes:
        module: The fully-qualified module name, resolved from `module="shell"` to
            `"flepimop2.process.shell"`.
        command: A single executable name or path, without shell quoting.
        args: Arguments to pass to the executable, including the script path.

    """

    command: str = Field(min_length=1)
    args: list[str] = Field(default_factory=list)

    @override
    def _process_validate(self) -> list[ValidationIssue]:
        """Diagnose combined commands while allowing executable paths with spaces.

        Returns:
            A validation issue when a whitespace-containing command cannot be
            resolved as a single executable or existing file.
        """
        if (
            any(char.isspace() for char in self.command)
            and not Path(self.command).is_file()
            and which(self.command) is None
        ):
            return [
                ValidationIssue(
                    msg=(
                        "`command` must be a single executable; put the script "
                        "and its arguments in `args`. An executable path with "
                        "spaces must exist and must not include shell quotes."
                    ),
                    kind="invalid_command",
                    ctx={"command": self.command},
                )
            ]
        return []

    def _process(self, *, dry_run: bool) -> None:
        """
        Execute a shell command.

        Raises:
            Flepimop2ValidationError: If the command combines an executable and
                arguments instead of naming a single executable.
            RuntimeError: If the command execution fails.
        """
        if issues := self._process_validate():
            raise Flepimop2ValidationError(issues)
        cmd = [self.command, *self.args]
        if dry_run:
            echo(shlex.join(cmd))
            return
        result = run(cmd, check=False)  # noqa: S603
        if result.returncode != 0:
            msg = f"Command failed with exit code {result.returncode}: {self.command}"
            raise RuntimeError(msg)
