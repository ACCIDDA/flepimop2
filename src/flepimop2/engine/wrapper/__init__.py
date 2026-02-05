"""A `EngineABC` which wraps a user-defined script file."""

__all__ = ["WrapperEngine"]

from pathlib import Path
from typing import Literal, Self

from pydantic import model_validator

from flepimop2._utils._module import _load_module, _validate_function
from flepimop2.configuration import ModuleModel
from flepimop2.engine.abc import EngineABC
from flepimop2.exceptions import ValidationIssue
from flepimop2.system.abc import SystemABC
from flepimop2.typing import StateChangeEnum


class WrapperEngine(ModuleModel, EngineABC):
    """A `EngineABC` which wraps a user-defined script file."""

    module: Literal["flepimop2.engine.wrapper"] = "flepimop2.engine.wrapper"
    state_change: StateChangeEnum
    script: Path

    @model_validator(mode="after")
    def _validate_script(self) -> Self:
        mod = _load_module(self.script, "flepimop2.engine.wrapped")
        if not _validate_function(mod, "runner"):
            msg = f"Module at {self.script} does not have a valid 'runner' function."
            raise AttributeError(msg)
        self._runner = mod.runner
        return self

    def validate_system(self, system: SystemABC) -> list[ValidationIssue] | None:
        """
        Validate that the given system is compatible with this engine.

        Args:
            system: The system to validate.

        Returns:
            A list of validation issues, or `None` if not implemented.

        """
        if system.state_change != self.state_change:
            return [
                ValidationIssue(
                    msg=(
                        f"Engine state change type, '{self.state_change}', is not "
                        "compatible with system state change type "
                        f"'{system.state_change}'."
                    ),
                    kind="incompatible_system",
                )
            ]
        return None
