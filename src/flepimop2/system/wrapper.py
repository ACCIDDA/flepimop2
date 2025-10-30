"""A `SystemABC` which wraps a user-defined script file."""

from os import PathLike

from flepimop2._utils._module import _load_module, _validate_function
from flepimop2.system import SystemABC


class WrapperSystem(SystemABC):
    """A `SystemABC` which wraps a user-defined script file."""

    def __init__(self, script: PathLike[str]) -> None:
        """
        Initialize a `WrapperSystem` from a script file.

        Args:
            script: Path to a script file which defines a 'stepper' function.

        Raises:
            AttributeError: If the module does not have a valid 'stepper' function.
        """
        mod = _load_module(script, "flepimop2.system.wrapped")
        if not _validate_function(mod, "stepper"):
            msg = f"Module at {script} does not have a valid 'stepper' function."
            raise AttributeError(msg)
        super().__init__(mod.stepper)


def build(script: PathLike[str]) -> WrapperSystem:
    """
    Build a `WrapperSystem` from a configuration arguments.

    Args:
        script: Path to a script file which defines a 'stepper' function.

    Returns:
        The constructed wrapper system instance.
    """
    return WrapperSystem(script)
