"""Shell process for flepimop2."""

from subprocess import run  # noqa: S404
from typing import Any, Literal

from pydantic import Field

from flepimop2.configuration import ModuleModel
from flepimop2.process.abc import ProcessABC


class ShellProcess(ModuleModel, ProcessABC):
    """
    Shell process for executing commands.

    Attributes:
        module: The module type, fixed to "shell".
        command: The shell command to execute.
        args: Arguments to pass to the shell command.
    """

    module: Literal["flepimop2.process.shell"] = "flepimop2.process.shell"
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


def build(config: dict[str, Any] | ModuleModel) -> ShellProcess:
    """
    Build a [`ShellProcess`][flepimop2.process.shell.ShellProcess] from a configuration.

    Args:
        config: Configuration dictionary to create a shell process. If module key is
            defined, it must be "shell". Must contain a 'command' key with the shell
            command to execute.

    Returns:
        The ready-to-use [`ShellProcess`][flepimop2.process.shell.ShellProcess]
            instance.
    """
    return ShellProcess.model_validate(
        config.model_dump() if isinstance(config, ModuleModel) else config
    )
