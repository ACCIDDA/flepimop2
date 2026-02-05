"""A `SystemABC` which wraps a user-defined script file."""

__all__ = ["WrapperSystem"]

from pathlib import Path
from typing import Any, Literal, Self

from pydantic import model_validator

from flepimop2._utils._module import _load_module, _validate_function
from flepimop2.configuration import ModuleModel
from flepimop2.system.abc import SystemABC
from flepimop2.typing import StateChangeEnum


class WrapperSystem(ModuleModel, SystemABC):
    """A `SystemABC` which wraps a user-defined script file."""

    module: Literal["flepimop2.system.wrapper"] = "flepimop2.system.wrapper"
    state_change: StateChangeEnum
    script: Path
    options: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _validate_stepper(self) -> Self:
        """
        Validator to load and validate the stepper function from the script file.

        Returns:
            The validated `WrapperSystem` instance.

        Raises:
            AttributeError: If the module does not have a valid 'stepper' function.
        """
        mod = _load_module(self.script, "flepimop2.system.wrapped")
        if not _validate_function(mod, "stepper"):
            msg = f"Module at {self.script} does not have a valid 'stepper' function."
            raise AttributeError(msg)
        self._stepper = mod.stepper
        return self
