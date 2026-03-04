"""A `SystemABC` which wraps a user-defined script file."""

__all__ = ["WrapperSystem"]

from pathlib import Path
from typing import Any, Literal, cast

from flepimop2._utils._module import _load_module, _validate_function
from flepimop2.configuration import ModuleModel
from flepimop2.system.abc import SystemABC, SystemProtocol
from flepimop2.typing import StateChangeEnum


class WrapperSystem(ModuleModel, SystemABC):
    """A `SystemABC` which wraps a user-defined script file."""

    module: Literal["flepimop2.system.wrapper"] = "flepimop2.system.wrapper"
    state_change: StateChangeEnum
    script: Path
    options: dict[str, Any] | None = None

    def build_stepper(self) -> SystemProtocol:
        """
        Load and validate the wrapped script stepper function.

        Returns:
            The validated stepper function from the wrapped script.

        Raises:
            AttributeError: If the module does not have a valid 'stepper' function.
        """
        mod = _load_module(self.script, "flepimop2.system.wrapped")
        if not _validate_function(mod, "stepper"):
            msg = f"Module at {self.script} does not have a valid 'stepper' function."
            raise AttributeError(msg)
        return cast("SystemProtocol", mod.stepper)
