"""Shell process for flepimop2."""

from subprocess import run  # noqa: S404
from typing import Any, Literal

from pydantic import Field

from flepimop2.configuration import ModuleModel
from flepimop2.process import ProcessABC


class ShellProcess(ModuleModel, ProcessABC):
    """Shell process for executing commands."""

    module: Literal["shell"] = "shell"
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


def build(config: dict[str, Any]) -> ShellProcess:
    """Build a `ShellProcess` from a configuration dictionary.

    Args:
        config (dict[str, any]):
            Configuration dictionary to create a shell process. If module key is
            defined, it must be "shell". Must contain a 'command' key with the shell
            command to execute.

    Returns:
        ProcessABC: the ready-to-use ShellProcess instance.
    """
    return ShellProcess(**config)
