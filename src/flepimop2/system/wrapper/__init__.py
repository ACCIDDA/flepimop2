"""A `SystemABC` which wraps a user-defined script file."""

__all__ = ["WrapperSystem"]

from pathlib import Path
from typing import Any, Literal, Self, override

from pydantic import PrivateAttr, model_validator

from flepimop2._utils._checked_partial import _checked_partial
from flepimop2._utils._module import _load_module, _validate_function
from flepimop2.configuration import ModuleModel
from flepimop2.configuration._types import IdentifierString
from flepimop2.system.abc import SystemABC
from flepimop2.typing import StateChangeEnum, SystemProtocol


class WrapperSystem(ModuleModel, SystemABC):
    """A `SystemABC` which wraps a user-defined script file."""

    module: Literal["flepimop2.system.wrapper"] = "flepimop2.system.wrapper"
    state_change: StateChangeEnum
    script: Path
    _stepper: SystemProtocol = PrivateAttr()

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

    @override
    def _bind_impl(
        self, params: dict[IdentifierString, Any] | None = None, **kwargs: Any
    ) -> SystemProtocol:
        return _checked_partial(
            func=self._stepper,
            forbidden={"time", "state"},
            params=params,
            **kwargs,
        )
