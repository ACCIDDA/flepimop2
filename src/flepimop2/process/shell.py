"""Shell process for flepimop2."""

from subprocess import CompletedProcess, run
from typing import Literal, Any

from pydantic import Field

from flepimop2.process import ProcessABC
from flepimop2.configuration import ModuleModel

class ShellProcess(ProcessABC, ModuleModel):
    """Shell process for executing commands."""

    module : Literal["shell"] = "shell"
    command : str = Field(min_length=1)
    
    def _process(self, *, dry_run : bool) -> None:
        """
        Execute a shell command.

        Raises:
            RuntimeError: If the command execution fails.
        """
        cmd = [self.command]
        if dry_run:
            cmd = ["echo"] + cmd
        
        result = run(" ".join(cmd), shell=True)
        if result.returncode != 0:
            raise RuntimeError(f"Command failed with exit code {result.returncode}: {self.command}")
        else:
            return


def build(config: dict[str, Any]) -> ShellProcess:
    """Build a `ShellProcess` from a configuration dictionary.

    Args:
        config (dict[str, any]):
            Configuration dictionary to create a shell process. If module key is
            defined, it must be "shell". Must contain a 'command' key with the shell command to execute.

    Returns:
        ProcessABC: the ready-to-use ShellProcess instance.
    """
    return ShellProcess(**config)
