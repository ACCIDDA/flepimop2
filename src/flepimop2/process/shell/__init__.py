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

from subprocess import run  # noqa: S404

from pydantic import Field

from flepimop2.configuration import ModuleModel
from flepimop2.process.abc import ProcessABC


class ShellProcess(ModuleModel, ProcessABC, module="shell"):
    """
    Shell process for executing commands.

    Attributes:
        module: The fully-qualified module name, resolved from `module="shell"` to
            `"flepimop2.process.shell"`.
        command: The shell command to execute.
        args: Arguments to pass to the shell command.

    """

    command: str = Field(min_length=1)
    args: list[str] = Field(default_factory=list)

    def _process(self, *, dry_run: bool) -> None:
        """
        Execute a shell command.

        Raises:
            RuntimeError: If the command execution fails.
        """
        cmd = [self.command, *self.args]
        if dry_run:
            cmd = ["echo", *cmd]
        cmd = " ".join(cmd).split(" ")
        result = run(cmd, check=False)  # noqa: S603
        if result.returncode != 0:
            msg = f"Command failed with exit code {result.returncode}: {self.command}"
            raise RuntimeError(msg)
