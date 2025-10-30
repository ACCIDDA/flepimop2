"""A `EngineABC` which wraps a user-defined script file."""

from os import PathLike

from flepimop2._utils._module import _load_module, _validate_function
from flepimop2.engine.abc import EngineABC


class WrapperEngine(EngineABC):
    """A `EngineABC` which wraps a user-defined script file."""

    def __init__(self, script: PathLike[str]) -> None:
        """
        Initialize a `WrapperEngine` from a script file.

        Args:
            script: Path to a script file which defines a 'runner' function.

        Raises:
            AttributeError: If the module does not have a valid 'runner' function.
        """
        mod = _load_module(script, "flepimop2.engine.wrapped")
        if not _validate_function(mod, "runner"):
            msg = f"Module at {script} does not have a valid 'runner' function."
            raise AttributeError(msg)
        super().__init__(mod.runner)


def build(script: PathLike[str]) -> WrapperEngine:
    """
    Build a `WrapperEngine` from a configuration arguments.

    Args:
        script: Path to a script file which defines a 'runner' function.

    Returns:
        The constructed wrapper engine instance.
    """
    return WrapperEngine(script)
